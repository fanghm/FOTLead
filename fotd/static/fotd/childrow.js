// Variable to keep track of the currently opened row, for hiding the child row only
var currentlyOpenedRow = null;

//var LinkCache = JSON.parse("{{ item_links|escapejs }}") - defined in backlog.html
if (LinkCache === null) {
    // console.log('No link data in db, initialize an empty object.');
    LinkCache = {'dirty': false};
}

function updateDatabaseViaAJAX() {
  if(LinkCache['dirty']) {
    console.log('Updating database via AJAX: ', FeatureId);
    $.ajax({
        type: "POST",
        url: `/ajax_update_item_links/${FeatureId}/`,
        data: JSON.stringify(LinkCache),
        contentType: "application/json",
        success: function(response) {
            LinkCache['dirty'] = false; // reset the dirty flag to avoid duplicate updates
            console.log("Links updated successfully:", response);
        },
        error: function(error) {
            console.error("Error updating links to db:", error);
        }
    });
  }
}

window.addEventListener('beforeunload', function(event) {
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
    function timeSince(date) {
        const now = new Date();
        const secondsPast = Math.floor((now - date) / 1000);

        if (secondsPast < 60) {
            return `${secondsPast} second${secondsPast > 1 ? 's' : ''} ago`;
        }
        if (secondsPast < 3600) {
            const minutes = Math.floor(secondsPast / 60);
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        }
        if (secondsPast < 86400) {
            const hours = Math.floor(secondsPast / 3600);
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        }
        if (secondsPast < 2592000) {
            const days = Math.floor(secondsPast / 86400);
            return `${days} day${days !== 1 ? 's' : ''} ago`;
        }
        if (secondsPast < 31536000) {
            const months = Math.floor(secondsPast / 2592000);
            return `${months} month${months !== 1 ? 's' : ''} ago`;
        }
        const years = Math.floor(secondsPast / 31536000);
        return `${years} year${years !== 1 ? 's' : ''} ago`;
    }

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
    let links = linkData["links"];
    let link_prefix = "https://jiradc.ext.net.nokia.com/browse/";

    let queryTime = "";
    if ("timestamp" in linkData && linkData["timestamp"]) {
        let date = new Date(linkData["timestamp"]);
        queryTime = timeSince(date);
        queryTime += "&nbsp;";
    }

    let refreshHtml = `
            ◴ Data Time: ${queryTime}
            <button class="refreshLinks">↻ Refresh</button>
            <input type="checkbox" id="showDoneChildItems"> Show done items
    `;

    // if links is empty, return directly
    if (links && links.length === 0) {
        return `<div style="padding-left: 40px;">
                    ⨂ Child item not created, or all are closed.<br>
                    ${refreshHtml}
                </div>`;
    }

    let link_details = links.map(link => {
        // Calculate Total_Effort
        let total_effort = (link.Logged_Effort || 0) + (link.Time_Remaining || 0);

        // Change Status to "Delayed" if End_FB > RC_FB
        let status = link.Status;
        if (link.RC_FB && link.End_FB && link.End_FB > link.RC_FB) {
            status = "Delayed";
            var status_cls = "delayed";
        }

        // Concatenate the last four fields into a "Comment" column
        let comment = [link.Team, link.Risk_Status, link.FB_Committed_Status, link.TC_Number]
            .filter(field => field && field.trim() !== "")
            .join(", ");

        return `<tr>
                    <td>${link.Relationship}</td>
                    <td>${link.Item_Type}</td>
                    <td><a href="${link_prefix}${link.Key}" title="${escapeHtml(link.Summary)}" target="_blank">${link.Key}</a></td>
                    <td class="${status_cls}">${status}</td>
                    <td>${link.Assignee}</td>
                    <td>${link.Start_FB}</td>
                    <td>${link.End_FB}</td>
                    <td>${total_effort}</td>
                    <td>${link.Time_Remaining !== undefined ? link.Time_Remaining : ''}</td>
                    <td>${comment}</td>
                </tr>`;
    });

    let linkDetailsHtml = link_details.join('');
    let rep = linkData["rep"];
    if (rep) {
        linkDetailsHtml += `<tr>
                              <td></td>
                              <td>ReP</td>
                              <td colspan="8"><a href="${rep}"" target="_blank">Test Execution Curve</a></td>
                            </tr>`;
    }

    linkDetailsHtml += `<tr>
                            <td colspan="10" style="text-align: right;">
                                ${refreshHtml}
                            </td>
                        </tr>`;

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


  // Add event listener for opening and closing details
  $('#backlog-table').on('click', 'td.dt-control', function (e) {
        if (typeof window.BacklogTable === 'undefined') {
            console.error('Fatal: DataTable is not yet initialized somehow.');
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
          if (key in LinkCache && 'links' in LinkCache[key]) {
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

function refreshLinkDetails(tr) {
    let id = tr.data('id');
    let key = tr.attr('id');
    let row = window.BacklogTable.row(tr);

    if (!key || !id) {
        console.error('Failed to get the key or id of the currently opened row.');
        return;
    }

    if (row.child.isShown()) {
        row.child.hide();
        currentlyOpenedRow = null;
    }

    console.log('Refresh link details for ' + key + ' with id ' + id);
    $('body').css('cursor', 'wait');
    $('#backlog-table').css('pointer-events', 'none');
    $.ajax({
        type: "GET",
        url: `/ajax_get_all_links/${id}/`,
        method: 'GET',
        success: function(linkData) {
            // replace the current child row with the updated one
            row.child(format(linkData)).show();
            currentlyOpenedRow = row;

            // Cache the details
            LinkCache[key] = linkData;
            LinkCache['dirty'] = true;
        },
        error: function() {
            currentlyOpenedRow = null;
            alert('Failed to load details');
        },
        complete: function() {
            // restore the cursor and enable table click events
            $('body').css('cursor', 'default');
            $('#backlog-table').css('pointer-events', 'auto');
        }
    });
}

  // use event delegation to catch the click event on the dynamically added link
  $(document).on('click', '.refreshLinks', function(e) {
      console.log('Refresh link details');
      e.preventDefault();

      let tr = null;
      let clicked = $(this);

      // distinguish between the two types of rows
      if (clicked.closest('td').attr('colspan') === '10') {
        tr = clicked.closest('tr').closest('td').closest('tr').prevAll('.dt-hasChild').first();
      } else {
        tr = clicked.closest('tr').prevAll('.dt-hasChild').first();
      }

      if (tr.length === 0) {
            console.error('No parent <tr> with class "dt-hasChild" found.');
            return;
        }

        refreshLinkDetails(tr);
    });

});
