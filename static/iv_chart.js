function render_chart(data) {
    reset_chart();

    const ticker = data.ticker;
    // console.log(data.average_ivs);
    const ivs_averages = data.average_ivs.map(arr => parseFloat(arr.average));
    const timestamps = data.average_ivs.map(arr => arr.scraper_timestamp_pretty);
    const mean = data.mean;
    const median = data.median;

    const percentage = 0.85;
    const min_iv_averages = Math.min(...ivs_averages);
    const iv_padding = min_iv_averages * (1 - percentage);

    const chart = new Chart(document.getElementById("line-chart"), {
        type: 'line',
        data: {
            datasets: [{
                data: data.average_ivs,
                label: 'IV %',
                borderColor: 'blue',
                fill: 'origin'
            }]
        },
        options: {
            parsing: {
                xAxisKey: 'scraper_timestamp',
                yAxisKey: 'average'
            },
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: ticker + ' IV history',
                    font: {
                        size: 24,
                        weight: 'bold'
                    },
                    align: 'end'
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function (context) {
                            return context[0].raw.created_at_pretty;
                        },
                        footer: function (context) {
                            return "Expiration: " + context[0].raw.expires_at;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        lineMean: {
                            type: 'line',
                            label: {
                                content: "Mean: " + parseFloat(mean).toFixed(2) + "%",
                                display: true,
                                position: "start",
                                z: 1,
                                backgroundColor: 'rgba(153, 102, 255,0.8)',
                                xAdjust: 5
                            },
                            yMin: mean,
                            yMax: mean,
                            borderColor: 'rgb(153, 102, 255)',
                            borderWidth: 2,
                        },
                        lineMedian: {
                            type: 'line',
                            label: {
                                content: "Median: " + parseFloat(median).toFixed(2) + "%",
                                display: true,
                                position: "start",
                                z: 1,
                                backgroundColor: 'rgba(255, 99, 132,0.8)',
                                xAdjust: 110,
                            },
                            yMin: median,
                            yMax: median,
                            borderColor: 'rgb(255, 99, 132)',
                            borderWidth: 2,
                        }
                    }
                },
                // interaction: {
                //     mode: 'nearest',
                //     axis: 'x',
                //     intersect: false
                // },
                // decimation: {
                //     enabled: true,
                //     algorithm: 'lttb',
                //     samples: 50,
                //     threshold: 50,
                // }
            },
            scales: {
                x: {
                    // type: 'time',
                    // time: {
                    //     unit: 'day',
                    //     displayFormats: {
                    //         day: 'D MMM yyyy'
                    //     },
                    //     tooltipFormat: 'D MMM yyyy'
                    // },
                    ticks: {
                        callback: function (value, index, ticks) {
                            return timestamps[index];
                        },
                        maxTicksLimit: 12
                    },

                },
                y: {
                    title: {
                        display: true,
                        text: 'Implied Volatility %'
                    },
                    max: Math.round(Math.max(...ivs_averages) + iv_padding),
                    min: Math.round(Math.min(...ivs_averages) - iv_padding)
                }
            },
            layout: {
                padding: {
                    right: 50,
                    left: 50,
                    top: 20,
                    bottom: 80
                }
            },
            tension: 0.4
        }
    });
}

function reset_chart() {
    const canvas_html = '<canvas id="line-chart"></canvas>';
    $("#line-chart").remove();
    $("#canvas-container").append(canvas_html);
}
