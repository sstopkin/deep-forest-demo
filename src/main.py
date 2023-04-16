import io

import uvicorn
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette import status


from PIL import Image
import matplotlib.pyplot as plt
from matplotlib import rcParams

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
async def recoginze(
        file: UploadFile
    ):
    try:
        file_content = await file.read()

        image = Image.open(io.BytesIO(file_content))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        # image.save('orig.jpg', 'JPEG', quality=50)
        print(image.format, image.size, image.mode)

        # plt.show()
        rcParams['figure.figsize'] = 20, 40

        numpydata = np.asarray(image)

        boxes = model.predict_image(numpydata)
        boxes.head()

        boxes_count = len(boxes)

        plot = model.predict_image(numpydata, return_plot=True, thickness=3)

        fig, axs = plt.subplots()
        axs.imshow(plot[:,:,::-1])
        axs.set_title(f"Количество деревьев на изображении: {boxes_count}")
        axs.set_xticks([])
        axs.set_yticks([])

        # plt.show()

        with io.BytesIO() as buff:
            fig.savefig(buff, format='raw')
            buff.seek(0)
            data = np.frombuffer(buff.getvalue(), dtype=np.uint8)
        w, h = fig.canvas.get_width_height()
        bytes_img = data.reshape((int(h), int(w), -1))

        result_image = Image.fromarray(bytes_img).convert('RGB')
        # image.save('out.jpg', 'JPEG', quality=50)
        
        with io.BytesIO() as buf:
            result_image.save(buf, format='JPEG')
            im_bytes = buf.getvalue()
        
        headers = {'DF-Filename': file.filename, 'DF-Boxes-Count': str(boxes_count)}
        # headers = {'Content-Disposition': 'inline; filename="test.png"'}
        return Response(im_bytes, headers=headers, media_type='image/jpeg')
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error"
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
