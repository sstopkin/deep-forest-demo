const axios = window.axios;

$(() => {
    const form = $("#form");
    const fileInput = $("#file");
    const submitBtn = $("#submit-btn");
    const goBackBtn = $("#go-back-btn");
    const progressBarUploadDiv = $("#progressBarUploadDiv");
    const progressBarUploadBar = $("#progressBarUploadBar");
    const result = $("#result");


    function handleError(error) {
        console.error("Произошла ошибка: " + error);
        submitBtn.prop("disabled", false);
        progressBarUploadDiv.hide();
    }

    async function getData(formData) {
        try {
            const response = await axios.post("http://localhost:8080/api/v1/recognize", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
                onUploadProgress: function (e) {
                    if (e.event.lengthComputable) {
                        const percent = (e.event.loaded / e.event.total) * 100;
                        progressBarUploadBar.attr("aria-valuenow", percent).css("width", percent + "%");
                    }
                },
                responseType: 'blob',
            })
            if (response.status != 200) {
                // test for status you want, etc
                console.log(response.status)
                throw new Error();
            }
            // Don't forget to return something   
            return response
        }
        catch (error) {
            handleError(error);
            console.error(error);
        }
    }

    submitBtn.on("click", async (e) => {
        submitBtn.prop("disabled", true);
        form.hide();
        progressBarUploadDiv.show();

        const file = fileInput[0].files[0];
        const formData = new FormData();
        formData.append("file", file);

        getData(formData)
            .then((response) => {
                progressBarUploadDiv.hide()
                goBackBtn.show();
                const treeCount = response.headers["df-boxes-count"];
                const urlCreator = window.URL || window.webkitURL;
                const imageUrl = urlCreator.createObjectURL(response.data);
                const img = new Image();
                img.onload = function () {
                    result.empty();
                    result.append(`<p>Количество деревьев на изображении: ${treeCount}</p>`);
                    result.append(img);
                    submitBtn.prop("disabled", false);
                };
                img.src = imageUrl;
            })
            .catch(function (error) {
                console.error("Произошла ошибка: " + error);
                submitBtn.prop("disabled", false);
                progressBarUploadDiv.hide();
                goBackBtn.show();
            });
    });

    goBackBtn.on("click", async (e) => {
        form.show();
        result.hide();
        fileInput.val("");
        goBackBtn.hide();
    });
});
