$(document).ready(function() {
  // Get the number of columns
  // -1 because of the colspan th is not a real column
  var numColumns = $('#backlog-table thead th').length - 1;

  // Generate an array of column indexes from 10 to the last column
  var nonSortableColumns = Array.from({length: numColumns - 11}, (_, i) => i + 11);
  //console.log('Number of columns:', numColumns);
  //console.log('Non-sortable columns:', nonSortableColumns);

  // add <tfoot> tag with same number of <th></th> as the table columns
  var tfoot = '<tfoot>';
  for (var i=0; i<numColumns; i++)
    tfoot += '<th></th>';

  tfoot += '</tfoot>';

  $("#backlog-table").append(tfoot);

    // Initialize the DataTable
    window.BacklogTable = $('#backlog-table').DataTable({
        ordering: true,
        order: [[6, "asc"], [3, "asc"]],
        responsive: true,
        //orderFixed: [1, 'asc'],
        rowGroup: { enable: false, dataSrc: 11 },
        //"stateSave": true,
        "scrollX": true,
        "sScrollXInner": "100%",  // if scrollX is true without this line, table body and header might not align
        "scrollY": true,
        "pageLength": -1,
        //"lengthChange": false, // dont show "Show xx entries" by default
        "pagingType": "simple", // use simple pagination

        layout: {
            topStart: {
                buttons: [
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
                            text: 'System Item',
                            action: function (e, dt, node, config) {
                              _group_by(dt, 11);
                            }
                        },
                        {
                            text: 'Entity Item',
                            action: function (e, dt, node, config) {
                              _group_by(dt, 12);
                            }
                        },
                        {
                            text: 'Activity Type',
                            action: function (e, dt, node, config) {
                              _group_by(dt, 3);
                            }
                        },
                        {
                            text: 'Competence Area',
                            action: function (e, dt, node, config) {
                              _group_by(dt, 2);
                            }
                        },
                        {
                            text: 'None',
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
                              filename: FeatureId + '_backlog_' + new Date().toLocaleString(),
                              footer: false,
                          },
                          {
                              extend: 'pdfHtml5',
                              title: `Feature Backlog - ${FeatureId}`,
                              messageBottom: function() {
                                  return '(Exported at ' + new Date().toLocaleString() + ')';
                              },
                              orientation: 'landscape',
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
                  },
                  {
                    text: 'Table control',
                    extend: 'collection',
                    autoClose: true,
                    buttons: [
                        // {
                        //     text: 'Toggle 1-2',
                        //     action: function ( e, dt, node, config ) {
                        //         dt.column( 1 ).visible( ! dt.column( 1 ).visible() );
                        //         dt.column( 2 ).visible( ! dt.column( 2 ).visible() );
                        //         this.active(!this.active());
                        //     }
                        // },
                        {
                            text: 'Classic View',
                            action: function ( e, dt, node, config ) {
                              for (col of nonSortableColumns)
                                dt.column(col).visible( !dt.column(col).visible() );

                              dt.column(0).visible( ! dt.column( 0 ).visible() );   // hide child rows
                              dt.column(9).visible( ! dt.column( 9 ).visible() );   // hide RC Status column
                              dt.column(10).visible( ! dt.column( 10 ).visible() ); // hide progress column
                              dt.column(11).visible(false); // hide sub-feature column
                              dt.column(12).visible(false); // hide EI column
                              dt.column(13).visible( ! dt.column( 13 ).visible() ); // hide ReP column
                              this.active(!this.active());
                            }
                        },
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

        "columnDefs": [
          {
            targets: [11, 12, 13],  // hide the SI/EI/Rep columns
            visible: false
          },

          // make the fb columns not sortable
          //{ "orderable": false, "targets": nonSortableColumns },

          // center the start/end fb and totol/remaining effort columns
          // TODO: not working somehow
          {
            "targets": [5,6,7,8],
            "className": "center-align"
          },
        ],

        // "drawCallback": function(settings) {
        //   var api = this.api();
        //   if (api.page.info().pages <= 1) {
        //     $('#' + api.table().node().id + '_paginate').hide(); // hide pagination if only one page
        //   } else {
        //     $('#' + api.table().node().id + '_paginate').show();
        //   }
        //   if (api.page.info().recordsTotal < 20) {
        //     $('#' + api.table().node().id + '_length').hide(); // if record number less than 20, hide "Showing xx entries" dropdown
        //   } else {
        //     $('#' + api.table().node().id + '_length').show();
        //   }
        // },

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

          // Total over all pages
          total_effort = api.column(7).data().reduce((a, b) => intVal(a) + intVal(b), 0);
          total_remaining = api.column(8).data().reduce((a, b) => intVal(a) + intVal(b), 0);

          // count the number of unique Competence Areas
          let caValues = api.column(2).data().toArray();
          let uniqueCaValues = new Set(caValues);
          let uniqueCaCount = uniqueCaValues.size;

          // Calculate the percentage of rows with "Ready for Commitment" in the RC_Status column
          let totalRows = api.column(9).data().length;
          let rfcCount = api.column(9).data().filter(text => text === "Ready for Commitment").length;
          let rfcOrCommittedCount = api.column(9).data().filter(text => text === "Ready for Commitment" || text.startsWith("Committed")).length;
          let rfcPercentage = (rfcOrCommittedCount / totalRows * 100).toFixed(0);
          let donePercentage = ((total_effort - total_remaining) / total_effort * 100).toFixed(1);

          // Update footer
          api.column(2).footer().innerHTML = `${uniqueCaCount} Areas`;
          api.column(4).footer().innerHTML = '<button id="copyToClipboard">Copy All Names</button>';
          api.column(7).footer().innerHTML = `${total_effort} Hrs`;
          api.column(8).footer().innerHTML = `${total_remaining} Hrs`;
          api.column(9).footer().innerHTML = `${rfcPercentage}% ` + (rfcCount > 0 ? 'RfC' : 'Committed');
          api.column(10).footer().innerHTML = `${donePercentage}% Done`;
        },

      });

  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('query_done')) {
      $('#showDoneItems').prop('checked', (urlParams.get('query_done') === 'true'));
  }

  $('#showDoneItems').change(function() {
    var queryDoneUrl = new URL(window.location.href);
      queryDoneUrl.searchParams.set('query_done', this.checked ? 'true' : 'false');
      window.location.href = queryDoneUrl.toString();
  });

  function updateQueryUrls() {
      var currentUrl = new URL(window.location.href);
      var refreshUrl = new URL(currentUrl);
      var queryDoneUrl = new URL(currentUrl);

      refreshUrl.searchParams.set('refresh', '');

      var showDoneItemsChecked = $('#showDoneItems').is(':checked');
      queryDoneUrl.searchParams.set('query_done', showDoneItemsChecked ? 'true' : 'false');

      $('a#refreshLink').attr('href', refreshUrl.toString());
      $('a#queryDoneLink').attr('href', queryDoneUrl.toString());
  }

  updateQueryUrls();

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
  };

  // row grouping: change the fixed ordering when the data source is updated
  BacklogTable.on('rowgroup-datasrc', function (e, dt, val) {
      BacklogTable.order.fixed({ pre: [[val, 'asc']] }).draw();
  });

  // row group
  //BacklogTable._group_by(dt, 10);

  // Use event delegation to catch the click event on the dynamically added button
  $('body').on('click', '#copyToClipboard', function() {
    var columnData = BacklogTable.column(4).nodes().to$()
        .find('.hidden-assignee-for-copy')
        .map(function() {
            return $(this).text();
        }).get();

    var filteredData = columnData.filter(function(value) {
      return value.trim() !== "";
    });

    var uniqueData = [...new Set(filteredData)];
    var joinedData = uniqueData.join(';');

    navigator.clipboard.writeText(joinedData).then(function() {
      alert('All names copied to your clipboard!');
    }, function(err) {
      console.error('Could not copy text: ', err);
    });
  });


  const REQ_TYPE_PLANNING = "Planning";
  const REQ_TYPE_RFC = "RfC";
  function _send_mail_req(req_type, fid, area, item_keys, first_name, apo_email) {
    context = {
      'fid': fid,
      'area': area,
      'item_keys': item_keys,
      'first_name': first_name,
      'apo_email': apo_email
    };

    $.ajax({
      type: "POST",
      url: "/ajax_send_email/" + req_type + "/",
      data: JSON.stringify(context),
      contentType: "application/json",
      success: function(response) {
        console.log("Mail sent successfully:", response);
        alert(req_type + " mail sent successfully!");
      },
      error: function(error) {
        console.error("Error sending email:", error);
        alert("Failed to send email.");
      }
    });
  }

  $('.selectForEndFb').change(function() {
    var fid = $(this).data('fid');
    var area = $(this).data('area');
    var selectedOption = $(this).find('option:selected');

    var apo_email = selectedOption.data('apo_email');
    var apo = selectedOption.data('apo');
    var first_name = apo.split(' ')[0];

    var selectedValue = $(this).val();
    switch (selectedValue) {
      case 'requestPlanning':
        var item_key = $(this).data('item_key');
        console.log('Send a mail to Assignee/APO for planning of ', item_key);
        _send_mail_req(REQ_TYPE_PLANNING, fid, area, [item_key], first_name, apo_email);
        break;

    default:
      alert("Pls select an option.");
    }
  });

  $('.selectForRcStatus').change(function() {
    var fid = $(this).data('fid');
    var area = $(this).data('area');
    var selectedOption = $(this).find('option:selected');

    var apo_email = selectedOption.data('apo_email');
    var apo = selectedOption.data('apo');
    var first_name = apo.split(' ')[0];

    var selectedValue = $(this).val();
    switch (selectedValue) {
      case 'requestRfC':
        var item_key = $(this).data('item_key');
        console.log('Send a mail to Assignee/APO for RfC of ', item_key);
        _send_mail_req(REQ_TYPE_RFC, fid, area, [item_key], first_name, apo_email);
        break;

    case 'requestRfCAll':
      // iterate thru all items on the table and find out all the Keys with same Assignee and RC_Status is not set
      var keysWithSameAssigneeAndUnsetRCStatus = [];
      $('#backlog-table tr').each(function() {
        var row = $(this);
        var assignee = row.find('.assigneeCell').text();
        var rcStatus = row.find('.rcStatusCell').text();
        var key = row.find('.keyCell a').text();

        // 检查分配者电子邮件是否匹配且 RC_Status 未设置
        if (assignee.includes(apo) && rcStatus.includes('(Not Set)')) {
          keysWithSameAssigneeAndUnsetRCStatus.push(key);
        }
      });

      _send_mail_req(REQ_TYPE_RFC, fid, area, keysWithSameAssigneeAndUnsetRCStatus, first_name, apo_email);
      //console.log(keysWithSameAssigneeAndUnsetRCStatus);
      //alert("found keys: " + keysWithSameAssigneeAndUnsetRCStatus.length);
      break;

    default:
      alert("Pls select an option.");
    }
  });

  $('.selectForAssignee').change(function() {
    var selectedOption = $(this).find('option:selected');
    var selectedValue = $(this).val();
    var item_key = $(this).data('item_key');
    var lapo_email = selectedOption.data('lapo_email');

    switch (selectedValue) {
      case 'assignAPO':
        console.log('Update APO directly in JIRA', item_key);
        //refresh the page after that
        //break;
      case 'sendMail':
        console.log('Send a mail to L-APO for ', item_key);
        //break;

      default:
        console.log('Not implented yet.');
        alert("Not implented yet.");
    }
  });
});

$('#boundaryTable').DataTable({
  "paging": false,
  "ordering": false,
  "searching": false,
  "info": false
});
