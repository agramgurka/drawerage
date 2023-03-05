Chart.register(ChartDataLabels);

function initResultsScreen(results) {
    const previouslyInitedChart = Chart.getChart("results-canvas");
    if (previouslyInitedChart) previouslyInitedChart.destroy();


    let resultsAfter = results;
    let resultsBefore = [...resultsAfter].sort((a, b) => (b.result - b.round_increment) - (a.result - a.round_increment));
    let pointsBefore = [];
    let pointsAfter = []
    let increments = [];
    let labelsBefore = [];
    let labelsAfter = [];
    let backgroundColorsBefore = [];
    let backgroundColorsAfter = [];
    let incrementColors = []

    for (let i in resultsBefore) {
        labelsBefore.push(resultsBefore[i].player__nickname);
        pointsBefore.push(resultsBefore[i].result - resultsBefore[i].round_increment);
        backgroundColorsBefore.push(resultsBefore[i].player__drawing_color);
        increments.push(resultsBefore[i].round_increment);
        incrementColors.push(resultsBefore[i].player__drawing_color + 'CC');
    }

    for (let i in resultsAfter) {
        labelsAfter.push(resultsAfter[i].player__nickname);
        pointsAfter.push(resultsAfter[i].result);
        backgroundColorsAfter.push(resultsAfter[i].player__drawing_color);
    }

    const ctx = document.getElementById("results-canvas");

    const data = {
        labels: labelsBefore,
        datasets: [
            {
                maxBarThickness: 40,
                data: pointsBefore,
                backgroundColor: backgroundColorsBefore,
                borderRadius: 15,
                datalabels: {
                    labels: {
                        value: {
                            font: {size: 18},
                            align: 'end',
                            anchor: 'end',
                            color: 'black'
                        },
                        player: {
                            align: 'start',
                            anchor: 'start',
                            formatter: function(value, context) {
                                return context.dataset.labels !== undefined
                                       ? context.dataset.labels[context.dataIndex]
                                       : labelsBefore[context.dataIndex];
                            },
                            font: {size: 20},
                            color: 'black',
                        }
                    },
                },
            },
            {
                maxBarThickness: 40,
                data: 0,
                backgroundColor: incrementColors,
                borderRadius: 15,
                datalabels: {
                    labels: {
                        increment: {
                                font: {size: 18},
                                align: 'end',
                                anchor: 'end',
                                color: 'green',
                                backgroundColor: 'white',
                                borderRadius: 15,
                                formatter: function(value, context) {
                                    return value > 0 ? '+' + value : null;
                                }
                        },
                    }
                }
            }
        ],

    };

    const options = {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
                x: {
                    display: false,
                    stacked: true,
                },
                y: {
                    display: false,
                    stacked: true,
                }
              },
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                enabled: false,
            },
            datalabels: {
                color: 'white',
                display: true,
                font: {
                  weight: 'bold'
                },
            }
        },
        layout: {
            padding: {
                left: 100,
                right: 100,
                top: 50,
                bottom: 50
            }
        },
    };

    const config = {
            type: "bar",
            data: data,
            options: options,
    };

    let resultsChart = new Chart(ctx, config);
    setTimeout(
        function() {
        resultsChart.data.datasets[1].data = increments;
        resultsChart.data.datasets[0].datalabels.labels.value.display = false;
        resultsChart.update();
        }, 1500);
    setTimeout(
        function() {
            resultsChart.data.datasets.pop();
            resultsChart.data.datasets[0].data = pointsAfter;
            resultsChart.data.datasets[0].labels = labelsAfter;
            resultsChart.data.datasets[0].backgroundColor = backgroundColorsAfter;
            resultsChart.data.datasets[0].datalabels.labels.value.display = true;
            if (JSON.stringify(resultsBefore) === JSON.stringify(resultsAfter)) resultsChart.update('none');
            else resultsChart.update();
        }, 3000);

    return document.getElementById("results-screen");
};