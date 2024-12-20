
//var LinkCache = JSON.parse("{{ item_links|escapejs }}");
if (LinkCache === null) {
    // console.log('No link data in db, initialize an empty object.');
    LinkCache = {};
}

function updateDatabaseViaAJAX() {
  if(LinkCache['dirty']) {
    LinkCache['dirty'] = false; // reset the dirty flag to avoid multiple updates
    //var FeatureId = "{{ fid }}";

    console.log('Updating database via AJAX: ', FeatureId);
    $.ajax({
        type: "POST",
        url: `/ajax_update_item_links/${FeatureId}/`,
        data: JSON.stringify(LinkCache),
        contentType: "application/json",
        success: function(response) {
            console.log("Links updated successfully:", response);
        },
        error: function(error) {
            console.error("Error updating links to db:", error);
            LinkCache['dirty'] = true; // set the dirty flag back to true
        }
    });
  }
}

window.addEventListener('beforeunload', function(event) {
    // 执行一些清理操作
    console.log('beforeunload event triggered');
    //console.log(JSON.stringify(LinkCache));
    updateDatabaseViaAJAX();
});

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Tab is hidden');
        //console.log(JSON.stringify(LinkCache));
        updateDatabaseViaAJAX();
    } else {
        //console.log('Tab is visible');
    }
});

$(document).ready(function() {

    function escapeHtml(text) {
        if (!text) return text;
        return text.replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
      }

  // Formatting function for row details - modify as you need
  function format(linkData) {
    var links = linkData["links"];
    var rep = linkData["rep"];
    var link_prefix = "https://jiradc.ext.net.nokia.com/browse/";

    // if links is empty, return directly
    if (links.length === 0) {
        return '<ul><li>Child item not yet created, or all of them are done already. <a id="refreshLinks" href="#">Refresh</a></li></ul>';
    }

    var link_details = links.map(link => {
        // Calculate Total_Effort
        var total_effort = (link.Logged_Effort || 0) + (link.Time_Remaining || 0);

        // Change Status to "Delayed" if End_FB > RC_FB
        var status = link.End_FB > link.RC_FB ? "Delayed" : link.Status;

        // Concatenate the last four fields into a "Comment" column
        var comment = [link.Team, link.Risk_Status, link.FB_Committed_Status, link.TC_Number]
            .filter(field => field && field.trim() !== "")
            .join(", ");

        return `<tr>
                    <td>${link.Relationship}</td>
                    <td>${link.Item_Type}</td>
                    <td><a href="${link_prefix}${link.Key}" title="${escapeHtml(link.Summary)}" target="_blank">${link.Key}</a></td>
                    <td>${status}</td>
                    <td>${link.Assignee}</td>
                    <td>${link.Start_FB}</td>
                    <td>${link.End_FB}</td>
                    <td>${total_effort}</td>
                   <td>${link.Time_Remaining !== undefined ? link.Time_Remaining : ''}</td>
                    <td>${comment}</td>
                </tr>`;
    });

    let linkDetailsHtml = link_details.join('');
    if (rep) {
        linkDetailsHtml += `<tr>
                              <td></td>
                              <td>ReP</td>
                              <td colspan="8"><a href="${rep}"" target="_blank">Test Execution Curve</a></td>
                            </tr>`;
    }

    return `<table class="tight-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>Type</th>
                        <th>Key</th>
                        <th>Status</th>
                        <th>Assignee</th>
                        <th>Start FB</th>
                        <th>End FB</th>
                        <th>Total Effort</th>
                        <th>Time Remaining</th>
                        <th>Comment</th>
                    </tr>
                </thead>
                <tbody>
                    ${linkDetailsHtml}
                </tbody>
            </table>`;

}

  // Variable to keep track of the currently opened row
  var currentlyOpenedRow = null;

  // Add event listener for opening and closing details
  $('#backlog-table').on('click', 'td.dt-control', function (e) {
        if (typeof window.BacklogTable === 'undefined') {
            console.error('Fatal: DataTable is not yet initialized.');
            return;
        }

      let tr = $(e.target).closest('tr'); // conver tr to a jQuery object
      let id = tr.data('id');
      let key = tr.attr('id');
      let row = window.BacklogTable.row(tr);

      if (row.child.isShown()) {
          // This row is already open - close it
          row.child.hide();
          currentlyOpenedRow = null;
      } else {
          // Close the previously opened row if it exists
          if (currentlyOpenedRow && currentlyOpenedRow.child.isShown()) {
              currentlyOpenedRow.child.hide();
          }

          // set the cursor to wait and disable all click events in the table
          $('body').css('cursor', 'wait');
          $('#backlog-table').css('pointer-events', 'none');

          // Check if details are already cached
          if (key in LinkCache && 'links' in LinkCache[key] && LinkCache[key].links.length > 0) {
            console.log('Use cached link details for ' + key);
            row.child(format(LinkCache[key])).show();
            currentlyOpenedRow = row;

            // restore the cursor and enable table click events
            $('body').css('cursor', 'default');
            $('#backlog-table').css('pointer-events', 'auto');
          } else {
            console.log('Request link details via AJAX for ' + key);
            $.ajax({
                url: `/ajax_get_item_links/${id}/`,
                method: 'GET',
                success: function(linkData) {
                    row.child(format(linkData)).show();
                    currentlyOpenedRow = row;

                    // Cache the details
                    LinkCache[key] = linkData;
                    LinkCache['dirty'] = true;
                },
                error: function() {
                    alert('Failed to load details');
                },
                complete: function() {
                    // restore the cursor and enable table click events
                    $('body').css('cursor', 'default');
                    $('#backlog-table').css('pointer-events', 'auto');
                }
            });
        }
      }
  });

  // use event delegation to catch the click event on the dynamically added link
  $(document).on('click', '#refreshLinks', function(event) {
      console.log('Refresh link details');
      event.preventDefault();

      // get current open row's id
      let id = currentlyOpenedRow.data('id');
      let key = currentlyOpenedRow.data().ID;
      console.log('Refresh link details for ' + key);

      $.ajax({
          type: "GET",
          url: "/ajax_get_all_links/${id}/",
                method: 'GET',
                success: function(linkData) {
                    // replace the current child row with the updated one
                    currentlyOpenedRow.child(format(linkData)).show();

                    // Cache the details
                    LinkCache[key] = linkData;
                    LinkCache['dirty'] = true;
                },
                error: function() {
                    alert('Failed to load details');
                },
                complete: function() {
                    // restore the cursor and enable table click events
                    $('body').css('cursor', 'default');
                    $('#backlog-table').css('pointer-events', 'auto');
                }
      });
  });
});
