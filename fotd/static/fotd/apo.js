$(document).ready(function() {
    // Get the number of columns
    // -1 because of the colspan th is not a real column
    var numColumns = $('#apo-backlog-table thead th').length - 1;
    //   console.log('Number of columns:', numColumns);

    // Generate an array of column indexes for the effort distribution columns
    var colStart = 8;
    var dataColumns = Array.from({length: numColumns - colStart}, (_, i) => i + colStart);
    console.log('Effort columns:', dataColumns);

    // add <tfoot> tag with same number of <th></th> as the table columns
    var tfoot = '<tfoot>';
    for (var i=0; i<numColumns; i++)
    tfoot += '<th></th>';

    tfoot += '</tfoot>';

    $("#apo-backlog-table").append(tfoot);

    // Initialize the DataTable
    window.BacklogTable = $('#apo-backlog-table').DataTable({
        ordering: true,
        order: [[2, "asc"],[3, "asc"]], // default sorting by PSR, RC_Status
        responsive: true,
        //orderFixed: [1, 'asc'],
        //rowGroup: { enable: false, dataSrc: 11 },
        //"stateSave": true,
        "scrollX": true,
        "sScrollXInner": "100%",  // if scrollX is true without this line, table body and header might not align
        "scrollY": true,
        "pageLength": -1,
        //"lengthChange": false, // dont show "Show xx entries" by default
        "pagingType": "simple", // use simple pagination

        "columnDefs": [
            { width: '100px', targets: 1 },
            {
                targets: [0, 7],  // hide columns: key, total effort
                visible: false
            },

            {
                "targets": [2, 4, 5],
                "className": "center-align"
            },

            // make the fb columns not sortable
            //{ "orderable": false, "targets": dataColumns },
        ],

        // footer
        "footerCallback": function (row, data, start, end, display) {
            let api = this.api();
            let intVal = function (i) {
            return typeof i === 'string'
                ? i.replace(/[\$,\s]/g, '') * 1
                : typeof i === 'number'
                ? i
                : 0;
            };

            var effortData = [];
            dataColumns.forEach(function(col) {
                // Total over all pages
                total_effort = api.column(col).data().reduce((a, b) => intVal(a) + intVal(b), 0);
                //console.log(`total effort for column ${col}: ${total_effort}`);

                // Update footer
                api.column(col).footer().innerHTML = `${total_effort}`;

                // Collect effort data for the chart
                effortData.push(total_effort);
            });

            // get the FBs for the x-axis
            var fbs = [];
            $('table thead tr:nth-child(2) th').each(function() {
                fbs.push($(this).text());
            });

            // update the chart
            var ctx = document.getElementById('effortDistributionChart').getContext('2d');
            var effortDistributionChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: fbs,
                    datasets: [{
                        label: 'Effort Distribution',
                        data: effortData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'FB'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Effort'
                            }
                        }
                    }
                }
            });/*

            // 扩展 pdfHtml5 按钮
            $.fn.dataTable.ext.buttons.pdfHtml5.action = function(e, dt, button, config) {
                var canvas = document.getElementById('effortDistributionChart');
                var canvasImg = canvas.toDataURL("image/png", 1.0);

                // 获取表格数据
                var tableData = [];
                table.rows({ search: 'applied' }).every(function() {
                    var rowData = this.data();
                    tableData.push(rowData);
                });

                // 创建 PDF 文档定义
                var docDefinition = {
                    content: [
                        {
                            text: 'APO Dashboard',
                            style: 'header'
                        },
                        {
                            image: canvasImg,
                            width: 500
                        },
                        {
                            text: 'Table Data',
                            style: 'subheader'
                        },
                        {
                            table: {
                                headerRows: 1,
                                widths: Array(table.columns().header().length).fill('*'),
                                body: [
                                    // 表头
                                    table.columns().header().toArray().map(function(header) {
                                        return $(header).text();
                                    }),
                                    // 表格数据
                                    ...tableData
                                ]
                            }
                        },
                        {
                            text: '(Exported at ' + new Date().toLocaleString() + ')',
                            style: 'footer'
                        }
                    ],
                    styles: {
                        header: {
                            fontSize: 18,
                            bold: true,
                            margin: [0, 0, 0, 10]
                        },
                        subheader: {
                            fontSize: 15,
                            bold: true,
                            margin: [0, 10, 0, 5]
                        },
                        footer: {
                            fontSize: 10,
                            italics: true,
                            margin: [0, 10, 0, 0]
                        }
                    }
                };

                pdfMake.createPdf(docDefinition).download("APO_Dashboard.pdf");
            }; */

        },

        layout: {
            topStart: {
                buttons: [/*
                'pageLength',
                {
                    extend: 'spacer',
                    style: 'bar'
                },
                {
                    extend: 'collection',
                    autoClose: true,
                    text: 'Group by',
                    buttons: [
                        {
                            text: 'PSR',
                            action: function (e, dt, node, config) {
                            _group_by(dt, 2);
                            }
                        },
                        {
                            text: 'Team',
                            action: function (e, dt, node, config) {
                            _group_by(dt, -1);
                            }
                        }
                    ]
                },
                {
                    extend: 'collection',
                    autoClose: true,
                    text: 'Output',
                    buttons: [
                        'copy', // TODO: hide footer
                        {
                            extend: 'excelHtml5',
                            filename: 'APO_backlog_' + new Date().toLocaleString(),
                            footer: false,
                        },
                        {
                            extend: 'pdfHtml5',
                            title: `APO Dashboard`,
                            messageBottom: function() {
                                return '(Exported at ' + new Date().toLocaleString() + ')';
                            },
                            orientation: 'horizontal',
                            footer: false,
                            download: 'open',
                            exportOptions: {
                                columns: ':visible',
                                format: {
                                    body: function (data, row, column, node) {
                                    //console.log(`row ${row} col ${col}: ${data}`);
                                    return data.toLowerCase().includes('(not set)') ? '(Not Set)' : data.replace(/<[^>]+>/g, '');
                                    },
                                },
                            }
                        },
                    ]
                }, */
                {
                    text: 'Table control',
                    extend: 'collection',
                    autoClose: true,
                    buttons: [
                        {
                            popoverTitle: 'Visibility control',
                            extend: 'colvis',
                            collectionLayout: 'two-column',
                            exclude: [1, 11],
                        }
                    ]
                },
                ]
            }
        },

    });

    // for export
    var exportFormatter = {
        format: {
            body: function (data, row, column, node) {
                var strippedData = data.replace(/<[^>]+>/g, '');
                //console.log(`row ${row} col ${col}: ${strippedData}`);
                if(strippedData.toLowerCase().includes('(not set)')) {
                return "(Not Set)";
                } else {
                return strippedData;
                }
            }
        }
    };/*

    function _group_by(dt, dataColumn) {
        if(dataColumn === -1) { // no grouping
            if(dt.rowGroup().enabled()) {
            dt.rowGroup().disable().draw();
            }
        } else {
            if(!dt.rowGroup().enabled())
            dt.rowGroup().enable().draw();

            dt.rowGroup().dataSrc(dataColumn);
        }
    }

    // row grouping: change the fixed ordering when the data source is updated
    BacklogTable.on('rowgroup-datasrc', function (e, dt, val) {
        BacklogTable.order.fixed({ pre: [[val, 'asc']] }).draw();
    }); */

});
