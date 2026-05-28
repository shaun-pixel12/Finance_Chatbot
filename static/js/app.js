/* ==========================================================================
   app.js - 금융 AI 어시스턴트 프론트엔드 제어 스크립트
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // ── 1. 글로벌 상태 및 상수 ──────────────────────────────────────
    let chatMessages = []; // 대화 기록을 담을 배열
    let currentCharts = {}; // 생성된 Chart.js 객체 캐시
    let selectedMarketPeriod = "1mo"; // 기본 조회 기간: 1개월

    // 각 주식/환율/원자재 티커에 어울리는 테마 색상 정의 (기존 대시보드와 통일)
    const chartColors = {
        // 증시 지수
        "^KS11": "#FF6B6B",   // 코스피
        "^KQ11": "#4ECDC4",   // 코스닥
        "^GSPC": "#45B7D1",   // S&P 500
        "^IXIC": "#96CEB4",   // 나스닥
        "^DJI": "#FFEAA7",    // 다우존스
        // 환율
        "USDKRW=X": "#E74C3C", // 달러
        "EURKRW=X": "#3498DB", // 유로
        "JPYKRW=X": "#2ECC71", // 엔화
        // 원자재
        "GC=F": "#F39C12",    // 금
        "SI=F": "#BDC3C7",    // 은
        "CL=F": "#1ABC9C",    // 원유
    };

    // ── 2. DOM 요소 선택 ──────────────────────────────────────────
    // 탭 버튼 및 패널
    const menuItems = document.querySelectorAll(".menu-item");
    const tabPanels = document.querySelectorAll(".tab-panel");

    // 챗봇 요소
    const chatContainer = document.getElementById("chat-messages-container");
    const chatInput = document.getElementById("chat-input-field");
    const btnSend = document.getElementById("btn-send-message");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const suggestBtns = document.querySelectorAll(".suggest-btn");

    // 추천 종목 요소
    const btnRunRecommend = document.getElementById("btn-run-recommend");
    const recommendResultBox = document.getElementById("recommend-result-box");
    const periodRadioLabels = document.querySelectorAll("#recommend-period-group .radio-label");
    const marketRadioLabels = document.querySelectorAll("#recommend-market-group .radio-label");

    // 시장 현황 요소
    const marketPeriodGroup = document.getElementById("market-period-group");

    // ── 3. 공통 유틸리티 함수 ──────────────────────────────────────
    // 숫자에 쉼표 포맷 적용 (예: 12345.67 -> "12,345.67")
    function formatNumber(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return "N/A";
        return Number(num).toLocaleString("ko-KR", {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    // 마크다운 텍스트를 HTML로 파싱하여 렌더링 (marked.js 라이브러리 사용)
    function renderMarkdown(text) {
        if (typeof marked !== "undefined") {
            return marked.parse(text);
        }
        return text.replace(/\n/g, "<br>");
    }


    // ── 4. 탭 전환 기능 구현 ────────────────────────────────────────
    menuItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");

            // 모든 메뉴 버튼과 탭 패널에서 active 클래스 제거
            menuItems.forEach(btn => btn.classList.remove("active"));
            tabPanels.forEach(panel => panel.classList.remove("active"));

            // 선택한 탭 활성화
            item.classList.add("active");
            const targetPanel = document.getElementById(targetTab);
            if (targetPanel) {
                targetPanel.classList.add("active");
            }

            // 시장 현황 탭을 열었을 때 데이터 자동 로드
            if (targetTab === "tab-market") {
                loadMarketData();
            }
        });
    });


    // ── 5. AI 챗봇 탭 로직 ──────────────────────────────────────────
    // 환영 메시지 출력
    function renderWelcomeMessage() {
        const welcomeText = `안녕하세요! 🙋‍♂️ 저는 금융 AI 어시스턴트입니다.

한국·미국 주식, 환율, 원자재 등에 대해 물어보세요.
Yahoo Finance와 네이버 금융 데이터를 실시간으로 분석해드립니다!`;
        
        chatMessages = [{ role: "assistant", content: welcomeText }];
        chatContainer.innerHTML = "";
        appendMessageBubble("assistant", welcomeText);
    }

    // 메시지 풍선 화면에 추가
    function appendMessageBubble(role, content, isLoading = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", role);

        const headerDiv = document.createElement("div");
        headerDiv.classList.add("msg-header");
        
        if (role === "user") {
            headerDiv.innerHTML = `<span>나</span> <i class="fa-solid fa-user"></i>`;
        } else {
            headerDiv.innerHTML = `<i class="fa-solid fa-robot"></i> <span>금융 어시스턴트</span>`;
        }

        const bubbleDiv = document.createElement("div");
        bubbleDiv.classList.add("msg-bubble");
        
        if (isLoading) {
            bubbleDiv.classList.add("loading-bubble");
            bubbleDiv.innerHTML = `
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            `;
        } else {
            bubbleDiv.innerHTML = renderMarkdown(content);
        }

        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(bubbleDiv);
        chatContainer.appendChild(messageDiv);
        
        // 스크롤 아래로 고정
        chatContainer.scrollTop = chatContainer.scrollHeight;

        return messageDiv;
    }

    // 메시지 전송 처리 함수
    async function handleSendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // 1. 입력창 청소
        chatInput.value = "";

        // 2. 화면에 내 메시지 그리기 및 대화 기록에 저장
        appendMessageBubble("user", text);
        chatMessages.push({ role: "user", content: text });

        // 3. AI 로딩 풍선 띄우기
        const loadingBubble = appendMessageBubble("assistant", "", true);

        try {
            // 4. API 서버에 답변 요청
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: chatMessages })
            });

            if (!response.ok) {
                throw new Error("서버와의 통신이 원활하지 않습니다.");
            }

            const data = await response.json();
            
            // 5. 로딩 표시 지우고 실제 AI 답변 그리기
            loadingBubble.remove();
            appendMessageBubble("assistant", data.answer);
            chatMessages.push({ role: "assistant", content: data.answer });

        } catch (error) {
            console.error("챗봇 요청 실패:", error);
            loadingBubble.remove();
            
            const errorMsg = `⚠️ 오류가 발생했습니다: ${error.message}\n\n다시 질문해주세요.`;
            appendMessageBubble("assistant", errorMsg);
        }
    }

    // 대화 초기화
    function clearChatHistory() {
        if (confirm("대화 기록을 모두 삭제하시겠습니까?")) {
            renderWelcomeMessage();
        }
    }

    // 이벤트 리스너 바인딩 (챗봇)
    btnSend.addEventListener("click", handleSendMessage);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    btnClearChat.addEventListener("click", clearChatHistory);

    // 추천 질문 버튼 이벤트 바인딩
    suggestBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const question = btn.getAttribute("data-question");
            chatInput.value = question;
            handleSendMessage();
        });
    });

    // 화면 켜질 때 초기 챗봇 웰컴 메시지 출력
    renderWelcomeMessage();


    // ── 6. 추천 종목 탭 로직 ───────────────────────────────────────
    // 라디오 버튼 선택 시 활성화 상태 표시 디자인 제어
    function setupRadioGroup(labels, name) {
        labels.forEach(label => {
            const input = label.querySelector(`input[name="${name}"]`);
            label.addEventListener("click", () => {
                labels.forEach(l => l.classList.remove("active"));
                label.classList.add("active");
                input.checked = true;
            });
        });
    }

    setupRadioGroup(periodRadioLabels, "recommend-period");
    setupRadioGroup(marketRadioLabels, "recommend-market");

    // 추천 분석 시작 버튼 리스너
    btnRunRecommend.addEventListener("click", async () => {
        // 1. 선택 값 가져오기
        const selectedPeriod = document.querySelector('input[name="recommend-period"]:checked').value;
        const selectedMarket = document.querySelector('input[name="recommend-market"]:checked').value;

        // 2. 화면에 로딩 인디케이터 표시
        recommendResultBox.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-spinner fa-spin empty-icon" style="color: var(--accent-blue);"></i>
                <p>🤖 <strong>${selectedMarket}</strong>에 알맞은 <strong>${selectedPeriod}</strong> 추천 종목을 분석하고 있어요...</p>
                <p class="empty-sub">실시간 보고서 작성에 1~2분이 소요됩니다. 잠시만 기다려주세요.</p>
            </div>
        `;

        try {
            // 3. API 요청
            const response = await fetch("/api/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    period_label: selectedPeriod,
                    market_label: selectedMarket
                })
            });

            if (!response.ok) {
                throw new Error("분석을 진행할 수 없습니다. 잠시 후 다시 시도해 주세요.");
            }

            const data = await response.json();

            // 4. 결과 보고서 렌더링
            recommendResultBox.innerHTML = renderMarkdown(data.result);

        } catch (error) {
            console.error("종목 분석 실패:", error);
            recommendResultBox.innerHTML = `
                <div class="empty-state" style="color: var(--accent-red);">
                    <i class="fa-solid fa-triangle-exclamation empty-icon" style="color: var(--accent-red);"></i>
                    <p>⚠️ 분석 도중 문제가 발생했습니다.</p>
                    <p class="empty-sub">${error.message}</p>
                </div>
            `;
        }
    });


    // ── 7. 시장 현황 탭 로직 ───────────────────────────────────────
    // 기간 선택기 클릭 리스너
    if (marketPeriodGroup) {
        const periodBtns = marketPeriodGroup.querySelectorAll(".period-btn");
        periodBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                periodBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                selectedMarketPeriod = btn.getAttribute("data-period");
                
                // 기간 변경 시 차트만 리로드
                reloadCharts();
            });
        });
    }

    // 시장 데이터 통합 로드 (상단 카드 + 차트 전체)
    async function loadMarketData() {
        try {
            // 1. 실시간 지표 API 호출
            const response = await fetch("/api/market/current");
            if (!response.ok) throw new Error("실시간 시세 데이터를 불러오지 못했습니다.");
            const data = await response.json();

            // 2. 상단 숫자 카드 채우기
            renderMetrics("indices-metrics", data.indices);
            renderMetrics("exchange-metrics", data.exchange_rates, true); // 환율 여부=true
            renderMetrics("commodity-metrics", data.commodities);

            // 3. 차트 영역 구축 및 그리기
            buildChartLayouts("indices-charts", data.indices);
            buildChartLayouts("exchange-charts", data.exchange_rates);
            buildChartLayouts("commodity-charts", data.commodities);

        } catch (error) {
            console.error("시장 현황 로드 에러:", error);
            document.querySelectorAll(".metrics-grid").forEach(grid => {
                grid.innerHTML = `<p style="padding: 20px; color: var(--accent-red);">데이터를 불러오는 데 실패했습니다: ${error.message}</p>`;
            });
        }
    }

    // 실시간 수치 카드 렌더링
    function renderMetrics(containerId, categoryData, isExchange = false) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = "";

        Object.entries(categoryData).forEach(([name, info]) => {
            const price = info.price;
            const changePct = info.change_pct;
            
            // 등락에 따른 스타일 클래스 및 아이콘 설정
            let deltaClass = "neutral";
            let deltaIcon = "─";
            
            if (changePct > 0) {
                // 환율은 올라가는 것이 악재인 경우가 많지만, 화살표와 붉은색/초록색 시각화는 일반적인 등락 색상을 따릅니다.
                // 여기서는 Streamlit의 delta_color="inverse" 효과를 환율 탭에 부여해 보겠습니다.
                if (isExchange) {
                    deltaClass = "down"; // 환율 상승 = 위험(빨간색)
                    deltaIcon = "▲";
                } else {
                    deltaClass = "up"; // 주가 상승 = 호재(초록색)
                    deltaIcon = "▲";
                }
            } else if (changePct < 0) {
                if (isExchange) {
                    deltaClass = "up"; // 환율 하락 = 안정(초록색)
                    deltaIcon = "▼";
                } else {
                    deltaClass = "down"; // 주가 하락 = 악재(빨간색)
                    deltaIcon = "▼";
                }
            }

            // 환율의 경우 단위 원, 원자재는 $
            let unit = "";
            let decimalLength = 2;
            if (name.includes("달러") || name.includes("유로") || name.includes("엔화")) {
                unit = "원";
            } else if (containerId.includes("commodity")) {
                unit = "$";
                decimalLength = 2;
            }

            const metricCard = document.createElement("div");
            metricCard.classList.add("metric-card");
            metricCard.innerHTML = `
                <span class="metric-label">${name}</span>
                <span class="metric-value">${unit}${formatNumber(price, decimalLength)}</span>
                <span class="metric-delta ${deltaClass}">
                    ${deltaIcon} ${formatNumber(Math.abs(changePct), 2)}%
                </span>
            `;
            container.appendChild(metricCard);
        });
    }

    // 차트 레이아웃 뼈대 구축 및 그리기 트리거
    function buildChartLayouts(containerId, categoryData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = "";

        // 기존 생성된 차트 삭제 캐시 비우기
        Object.values(currentCharts).forEach(chart => {
            if (chart && chart.destroy) chart.destroy();
        });
        currentCharts = {};

        Object.entries(categoryData).forEach(([name, info]) => {
            const ticker = info.ticker;
            
            // 차트 카드 엘리먼트 생성
            const chartCard = document.createElement("div");
            chartCard.classList.add("chart-card");
            chartCard.innerHTML = `
                <div class="chart-header">
                    <span class="chart-title">${name} 추이</span>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="canvas-${ticker.replace(/[^a-zA-Z0-9]/g, '')}"></canvas>
                </div>
            `;
            container.appendChild(chartCard);

            // 차트 렌더링
            drawChart(ticker, name);
        });
    }

    // 개별 차트 렌더링 함수
    async function drawChart(ticker, name) {
        const canvasId = `canvas-${ticker.replace(/[^a-zA-Z0-9]/g, '')}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            // 과거 데이터 fetch
            const response = await fetch(`/api/market/history?ticker=${encodeURIComponent(ticker)}&period=${selectedMarketPeriod}`);
            if (!response.ok) throw new Error("역사 가격 데이터를 로드하지 못했습니다.");
            const data = await response.json();

            if (data.dates.length === 0) {
                const ctx = canvas.getContext("2d");
                ctx.fillStyle = "#64748b";
                ctx.font = "14px Inter";
                ctx.textAlign = "center";
                ctx.fillText("차트 데이터를 불러올 수 없습니다", canvas.width / 2, canvas.height / 2);
                return;
            }

            const color = chartColors[ticker] || "#00e5ff";
            const ctx = canvas.getContext("2d");

            // 배경 그라데이션 추가 (아름다운 시각 효과용)
            const gradient = ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, hexToRgbA(color, 0.25));
            gradient.addColorStop(1, hexToRgbA(color, 0.00));

            // Chart.js 인스턴스 생성
            currentCharts[ticker] = new Chart(canvas, {
                type: "line",
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: name,
                        data: data.prices,
                        borderColor: color,
                        borderWidth: 2,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.2, // 곡선 굴곡률 (부드러운 효과)
                        pointRadius: 0, // 기본 점 숨김
                        pointHoverRadius: 4, // 호버 시 점 표시 크기
                        pointHoverBackgroundColor: color,
                        pointHoverBorderColor: "#fff",
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            mode: "index",
                            intersect: false,
                            backgroundColor: "rgba(12, 16, 26, 0.9)",
                            titleColor: "#94a3b8",
                            bodyColor: "#f1f5f9",
                            borderColor: "rgba(255,255,255,0.08)",
                            borderWidth: 1,
                            titleFont: { family: "Inter", size: 11 },
                            bodyFont: { family: "Inter", size: 13, weight: "bold" },
                            callbacks: {
                                label: function(context) {
                                    return `종가: ${context.parsed.y.toLocaleString("ko-KR")}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            grid: { display: false },
                            ticks: {
                                maxTicksLimit: 6, // 날짜 라벨 수 제한
                                color: "#64748b",
                                font: { size: 10, family: "Inter" }
                            }
                        },
                        y: {
                            display: true,
                            grid: {
                                color: "rgba(255, 255, 255, 0.03)",
                                drawBorder: false
                            },
                            ticks: {
                                color: "#64748b",
                                font: { size: 10, family: "Inter" },
                                callback: function(value) {
                                    return value.toLocaleString("ko-KR");
                                }
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error(`차트 그리기 실패 (${name}):`, error);
        }
    }

    // 차트 기간만 변경되어 다시 로드하는 함수
    async function reloadCharts() {
        for (const ticker of Object.keys(currentCharts)) {
            // 기존 차트 제거
            if (currentCharts[ticker]) {
                currentCharts[ticker].destroy();
            }
            
            // 다시 그리기
            const name = Object.keys(chartColors).find(k => k === ticker) || ticker;
            drawChart(ticker, name);
        }
    }

    // 16진수 색상 코드를 rgba 형태로 만들어 투명도 줄 수 있는 헬퍼 함수
    function hexToRgbA(hex, alpha) {
        let c;
        if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
            c = hex.substring(1).split('');
            if (c.length == 3) {
                c = [c[0], c[0], c[1], c[1], c[2], c[2]];
            }
            c = '0x' + c.join('');
            return 'rgba(' + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') + ',' + alpha + ')';
        }
        return `rgba(0, 229, 255, ${alpha})`;
    }
});
