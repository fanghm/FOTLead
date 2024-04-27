$(document).ready(function() {
  // Initialize resizable columns
  $('#feature-table th').resizable({
    handles: 'e',
    stop: function(event, ui) {
      // Save column widths to local storage
      var columnWidths = {};
      $('#feature-table th').each(function() {
        columnWidths[$(this).data('resizable-column-id')] = $(this).width();
      });
      localStorage.setItem('columnWidths', JSON.stringify(columnWidths));
    }
  });

  // Load column widths from local storage
  var savedColumnWidths = localStorage.getItem('columnWidths');
  if (savedColumnWidths) {
    savedColumnWidths = JSON.parse(savedColumnWidths);
    $('#feature-table th').each(function() {
      var columnId = $(this).data('resizable-column-id');
      var width = savedColumnWidths[columnId];
      if (width) {
        $(this).width(width);
      }
    });
  }

  // Make table rows sortable
  var tbody = $('#feature-table tbody');
  tbody.sortable({
    axis: 'y',
    update: function(event, ui) {
      // Save the new order of rows to local storage
      var newOrder = [];
      $(this).find('tr').each(function() {
        newOrder.push($(this).find('td:first-child').text());
      });
      localStorage.setItem('tableRowsOrder', JSON.stringify(newOrder));
    }
  });

  // Load table rows order from local storage and adjust table rows accordingly
  var savedTableRowsOrder = localStorage.getItem('tableRowsOrder');
  if (savedTableRowsOrder) {
    savedTableRowsOrder = JSON.parse(savedTableRowsOrder);
    var rows = tbody.find('tr').get();
    tbody.empty();
    $.each(savedTableRowsOrder, function(index, id) {
      var row = rows.find(function(row) {
        return $(row).find('td:first-child').text() === id;
      });
      tbody.append(row);
    });
  }	
	
});
