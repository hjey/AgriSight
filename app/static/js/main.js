// 돔이 로드 되면,
document.addEventListener("DOMContentLoaded", () => {

    const select = document.getElementById("option-select");
    const input = document.getElementById("youtube-url");
    let url = document.getElementById("youtube-url");

    // 드롭 다운 && 직접 입력
    select.addEventListener("change", function () {
        if (select.value === "other") {
            input.disabled = false;  // 입력 가능
            input.classList.remove("bg-gray-200"); // 배경색 원래대로
        } else {
            input.disabled = true;   // 입력 불가능
            input.value = "";        // 기존 입력값 초기화
            input.classList.add("bg-gray-200"); // 시각적으로 비활성화 표시
        }
    });
    // https://youtu.be/7dETo7ECQKc?si=4Vc-zQlgT8YKoTFy
    // https://www.youtube.com/watch?v=7dETo7ECQKc


    //// 비디오 주소로 비디오 다운로드, 만약에 해당 코드가 디비에 없으면,

    //// 다운받은 코드의 자막을 생성, 디비에 저장(아래 추가하기, 새로 만들지 말고.)

    //// 해당 자막을 영상에 입힘, 그리고 저장 후 웹페이지에 로드.

    //// 로드하면서 세 모델 돌려서 띄우기

    const loadVideoButton = document.getElementById('loadVideoButton');
    const videoElement = document.getElementById("videoElement");
    let vid_id = '';
    let subtitles = []; // 자막 데이터 변수

    // 비디오 및 자막 로드
    loadVideoButton.addEventListener('click', function () {
        right_block.classList.add("divide-y", "divide-gray-300");

        if (select.value === "other") {
            let dict_url = url.value.split("/");

            if (url.value.includes('youtu.be')) {
                vid_id = dict_url[dict_url.length - 1].split('?');
                vid_id = vid_id[0];
            } else if (url.value.includes('youtube.com')) {
                vid_id = dict_url[dict_url.length - 1].split('=');
                vid_id = vid_id[vid_id.length - 1];
            }
            console.log('vid_id: ', vid_id)
            // 파일 유무 체크 후 if can download
            // 자막
            // DB
            // 합치기
            // 로드
            // 텍스트 모델 셋 로드
        } else {
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
        }
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
                    nerContainer.innerText = data.ner.map(k => k[0]).join(", ");
                } else {
                    nerContainer.innerText = "No NER found";
                }
            })
            .catch(error => {
                console.error("Error fetching NER:", error);
            });
    }

    // Summary 로드
    const summaryContainer = document.getElementById("summary");

    function getSummaryFromModel(videoId, language) {
        fetch(`/summary?video_id=${videoId}&language=${language}`)
            .then(response => response.json())
            .then(data => {
                if (data.ner) {
                    summaryContainer.innerText = data.summary.map(k => k[0]).join(", ");
                } else {
                    summaryContainer.innerText = "No Summary found";
                }
            })
            .catch(error => {
                console.error("Error fetching Summary:", error);
            });
    }

});
