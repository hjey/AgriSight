// 돔이 로드 되면,
document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("option-select");
    const loadVideoButton = document.getElementById('loadVideoButton');
    const videoElement = document.getElementById("videoElement");
    let subtitles = []; // 자막 데이터 변수

    // 비디오 및 자막 로드
    loadVideoButton.addEventListener('click', function () {
        right_block.classList.add("divide-y", "divide-gray-300");

        // 비디오 파일 로드
        videoElement.src = "http://127.0.0.1:8000/videos/" + select.value + "_trimmed_output.mp4";
        videoElement.classList.remove("hidden");  // 비디오가 보이도록 설정
        videoElement.play();  // 자동 재생

        // 자막 데이터베이스에서 자막 불러오기
        loadTitleFromDB(select.value, 'en');
        loadSubtitlesFromDB(select.value, 'en');
        getKeywordFromModel(select.value, 'en');
        getNERFromModel(select.value, 'en');
        getSummaryFromModel(select.value, 'en');
    });

    // 자막 데이터베이스에서 자막 불러오기
    function loadSubtitlesFromDB(videoId, language) {
        fetch(`/subtitles?video_id=${videoId}&language=${language}`)
            .then(response => response.json())
            .then(data => {
                subtitles = data; // 자막 데이터를 변수에 저장
            })
            .catch(error => {
                console.error('Error loading subtitles:', error);
            });
    }

    // 시간 로드
    const subtitlesContainer = document.getElementById("subtitle");
    // 비디오 시간에 맞는 자막 표시
    videoElement.addEventListener('timeupdate', function () {
        if (!subtitles.length) return;

        const currentTime = videoElement.currentTime;
        const currentSubtitle = subtitles.find(sub => {
            return currentTime >= sub.start_time && currentTime <= sub.end_time;
        });

        if (currentSubtitle) {
            subtitlesContainer.textContent = currentSubtitle.text;
        } else {
            subtitlesContainer.textContent = "";
        }
    });

    // 제목 로드
    const titleContainer = document.getElementById("title");
    function loadTitleFromDB(videoId) {
        fetch(`/title?video_id=${videoId}`)
            .then(response => response.json())
            .then(data => {
                if (data.title) {
                    titleContainer.textContent = data.title;
                } else {
                    titleContainer.textContent = "No title found";
                }
            })
            .catch(error => {
                console.error('Error loading title:', error);
            });
    }

    // 키워드 로드
    const keywordContainer = document.getElementById("keyword");

    function getKeywordFromModel(videoId, language) {
        fetch(`/keyword?video_id=${videoId}&language=${language}`)
            .then(response => response.json())
            .then(data => {
                if (data.keywords) {
                    keywordContainer.innerText = data.keywords.map(k => k[0]).join(", ");
                } else {
                    keywordContainer.innerText = "No keywords found";
                }
            })
            .catch(error => {
                console.error("Error fetching keywords:", error);
            });
    }

    // NER 로드
    const nerContainer = document.getElementById("ner");

    function getNERFromModel(videoId, language) {
        fetch(`/ner?video_id=${videoId}&language=${language}`)
            .then(response => response.json())
            .then(data => {
                if (data.ner) {
                    nerContainer.innerText = data.ner.map(k => k.word).join(", ");
                } else {
                    nerContainer.innerText = "No ner found";
                }
            })
            .catch(error => {
                console.error('Error loading NER:', error);
            });
    }


    // Summary 로드
    const summaryContainer = document.getElementById("summary");

    function getSummaryFromModel(videoId, language) {
        fetch(`/summary?video_id=${videoId}&language=${language}`)
            .then(response => response.json())
            .then(data => {
                if (data.summary) {
                    console.log('data.summary: ', data.summary)
                    summaryContainer.innerText = data.summary;
                } else {
                    summaryContainer.innerText = "No Summary found";
                }
            })
            .catch(error => {
                console.error("Error fetching Summary:", error);
            });
    }

});
