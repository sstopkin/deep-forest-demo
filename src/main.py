import io

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette import status


from PIL import Image
import matplotlib.pyplot as plt
from matplotlib import rcParams

from deepforest.visualize import plot_predictions
import numpy as np

from deepforest import main
from pylab import rcParams

log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

fast_api_app = FastAPI(openapi_url=None)

_api_app = FastAPI(
    title="DeepForest App",
    version="1.0.0",
    debug=True,
    docs_url="/docs"
)

model = main.deepforest()
model.use_release()

@_api_app.post("/recognize")
async def recoginze(file: UploadFile):
    try:
        model = main.deepforest()
        model.use_release()

        file_content = await file.read()

        image = Image.open(io.BytesIO(file_content)).convert("RGB")
        numpydata = np.asarray(image)

        boxes = model.predict_image(numpydata)

        if len(boxes):
            boxes_count = len(boxes)
        else:
            boxes_count = -1

        draw_image = np.asarray(image.copy())
        draw_image = plot_predictions(draw_image, boxes, thickness=3)
        draw_image = Image.fromarray(draw_image)

        with io.BytesIO() as buf:
            draw_image.save(buf, format="JPEG")
            im_bytes = buf.getvalue()

        headers = {'df-filename': file.filename, 'df-boxes-count': str(boxes_count)}
        return Response(im_bytes, headers=headers, media_type='image/jpeg')
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error"
        )
    finally:
        file.file.close()
        image.close()

fast_api_app.mount('/api/v1', _api_app)
fast_api_app.mount("/", StaticFiles(directory='web_app', html=True), name="static")

if __name__ == '__main__':
    uvicorn.run(
        'main:fast_api_app',
        host='0.0.0.0',
        port=8080,
        log_config=log_config,
        reload=True,
    )
