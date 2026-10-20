/**
 * AI-Powered Student Study Planner and Performance Analyzer
 * JavaScript UI Controllers & Chart.js Visualizations
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Sidebar Toggle
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const sidebar = document.getElementById("sidebar");

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener("click", () => {
            sidebar.classList.add("open");
        });
    }

    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener("click", () => {
            sidebar.classList.remove("open");
        });
    }

    // Close sidebar on clicking outside (mobile)
    document.addEventListener("click", (e) => {
        if (sidebar && sidebar.classList.contains("open")) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove("open");
            }
        }
    });

    // 2. Modal backdrop close
    const modals = document.querySelectorAll(".modal");
    modals.forEach((modal) => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.remove("show");
            }
        });
    });

    // 3. Asynchronous Task Status Toggling
    setupTaskToggleHandlers();
});

/**
 * Attaches AJAX submit handlers to task toggle checkboxes
 * Provides instant tactile feedback without page refresh.
 */
function setupTaskToggleHandlers() {
    const forms = document.querySelectorAll(".task-toggle-form");

    forms.forEach((form) => {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const btn = form.querySelector(".task-checkbox");
            const row = form.closest("tr") || form.closest(".task-item");
            const actionUrl = form.getAttribute("action");

            fetch(actionUrl, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json"
                }
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    const isCompleted = data.new_status === "Completed";

                    // Update button styling
                    if (isCompleted) {
                        btn.classList.add("checked");
                        if (row) {
                            row.classList.add("task-completed", "task-row-done");
                            const topicEl = row.querySelector(".task-topic-text") || row.querySelector(".task-topic");
                            if (topicEl) topicEl.classList.add("text-line-through", "text-muted");
                            const pill = row.querySelector(".task-status-pill");
                            if (pill) {
                                pill.textContent = "Completed";
                                pill.className = "task-status-pill status-done";
                            }
                        }
                    } else {
                        btn.classList.remove("checked");
                        if (row) {
                            row.classList.remove("task-completed", "task-row-done");
                            const topicEl = row.querySelector(".task-topic-text") || row.querySelector(".task-topic");
                            if (topicEl) topicEl.classList.remove("text-line-through", "text-muted");
                            const pill = row.querySelector(".task-status-pill");
                            if (pill) {
                                pill.textContent = "Pending";
                                pill.className = "task-status-pill status-pending";
                            }
                        }
                    }

                    // Update metric counters on tasks page if present
                    const metricTotal = document.getElementById("metricTotal");
                    const metricCompleted = document.getElementById("metricCompleted");
                    const metricPending = document.getElementById("metricPending");
                    const metricRate = document.getElementById("metricRate");
                    const metricRateBar = document.getElementById("metricRateBar");

                    if (metricTotal) metricTotal.textContent = data.total;
                    if (metricCompleted) metricCompleted.textContent = data.completed;
                    if (metricPending) metricPending.textContent = data.pending;
                    if (metricRate) metricRate.textContent = data.rate + "%";
                    if (metricRateBar) metricRateBar.style.width = data.rate + "%";
                }
            })
            .catch(() => {
                // If AJAX fails, submit standard form
                form.submit();
            });
        });
    });
}

// -------------------------------------------------------------
// Chart.js Visualizations
// -------------------------------------------------------------

/**
 * Initializes charts on the main student dashboard
 */
function initDashboardCharts() {
    fetch("/api/chart-data")
        .then((res) => res.json())
        .then((data) => {
            // 1. Task Completion Doughnut Chart
            const tasksCanvas = document.getElementById("tasksDoughnutChart");
            if (tasksCanvas && data.tasks) {
                new Chart(tasksCanvas, {
                    type: "doughnut",
                    data: {
                        labels: ["Completed", "Pending"],
                        datasets: [{
                            data: [data.tasks.completed, data.tasks.pending],
                            backgroundColor: ["#10b981", "#f59e0b"],
                            borderWidth: 2,
                            borderColor: "#ffffff",
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        const total = data.tasks.total || 1;
                                        const pct = Math.round((ctx.parsed / total) * 100);
                                        return ` ${ctx.label}: ${ctx.parsed} tasks (${pct}%)`;
                                    }
                                }
                            }
                        },
                        cutout: "68%"
                    }
                });
            }

            // 2. Performance Bar Chart
            const perfCanvas = document.getElementById("performanceBarChart");
            if (perfCanvas && data.performance) {
                renderPerformanceBar(perfCanvas, data.performance);
            }
        })
        .catch((err) => console.error("Error loading dashboard chart data:", err));
}

/**
 * Initializes the Subject Preparation Level chart on the Subjects page
 */
function initPreparationChart() {
    fetch("/api/chart-data")
        .then((res) => res.json())
        .then((data) => {
            const canvas = document.getElementById("preparationBarChart");
            if (canvas && data.preparation) {
                new Chart(canvas, {
                    type: "bar",
                    data: {
                        labels: data.preparation.labels,
                        datasets: [{
                            label: "Current Preparation %",
                            data: data.preparation.percentages,
                            backgroundColor: data.preparation.percentages.map((p) => {
                                if (p < 40) return "#ef4444";
                                if (p < 70) return "#f59e0b";
                                return "#10b981";
                            }),
                            borderRadius: 6
                        }]
                    },
                    options: {
                        indexAxis: "y",
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                min: 0,
                                max: 100,
                                ticks: { callback: (val) => val + "%" },
                                grid: { color: "#f1f5f9" }
                            },
                            y: { grid: { display: false } }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }
        })
        .catch((err) => console.error("Error loading preparation chart:", err));
}

/**
 * Initializes the Subject Time Allocation Doughnut on the Study Plan page
 */
function initStudyPlanChart() {
    fetch("/api/chart-data")
        .then((res) => res.json())
        .then((data) => {
            const canvas = document.getElementById("studyPlanPieChart");
            if (canvas && data.study_plan) {
                const palette = [
                    "#4f46e5", "#06b6d4", "#f59e0b", "#ec4899", 
                    "#10b981", "#8b5cf6", "#64748b"
                ];

                new Chart(canvas, {
                    type: "pie",
                    data: {
                        labels: data.study_plan.labels,
                        datasets: [{
                            data: data.study_plan.allocated_hours,
                            backgroundColor: palette.slice(0, data.study_plan.labels.length),
                            borderWidth: 2,
                            borderColor: "#ffffff"
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: "bottom",
                                labels: { boxWidth: 12, font: { size: 11 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        return ` ${ctx.label}: ${ctx.parsed} hrs/week`;
                                    }
                                }
                            }
                        }
                    }
                });
            }
        })
        .catch((err) => console.error("Error loading study plan chart:", err));
}

/**
 * Initializes the Performance Comparison Chart on the Performance page
 */
function initPerformanceChart() {
    fetch("/api/chart-data")
        .then((res) => res.json())
        .then((data) => {
            const canvas = document.getElementById("performanceBarChart");
            if (canvas && data.performance) {
                renderPerformanceBar(canvas, data.performance);
            }
        })
        .catch((err) => console.error("Error loading performance chart:", err));
}

/**
 * Shared helper to render performance bar charts
 */
function renderPerformanceBar(canvas, perfData) {
    new Chart(canvas, {
        type: "bar",
        data: {
            labels: perfData.labels,
            datasets: [{
                label: "Average Marks (%)",
                data: perfData.averages,
                backgroundColor: perfData.averages.map((avg) => {
                    if (avg >= 75) return "#10b981"; // Strong
                    if (avg >= 50) return "#f59e0b"; // Moderate
                    return "#ef4444"; // Weak
                }),
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: { callback: (val) => val + "%" },
                    grid: { color: "#f1f5f9" }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            return ` Score: ${ctx.parsed.y}%`;
                        }
                    }
                }
            }
        }
    });
}
