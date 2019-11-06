var selections = [];

function GetDataFromDB(){
	$('#listTable').bootstrapTable({
		url : '/getLog',
		dataType : 'json',
		columns : [{
			field: 'state',
			checkbox: true,
			align: 'center',
			valign: 'middle',
		},{
			title: 'ID',
			field: 'Id',
			sortable: true,
		},{
			title: 'Information',
			field: 'Information',
		},{
			title: 'Source',
			field: 'Source',
			sortable: true,
		},{
			title: 'Status',
			field: 'Status',
			sortable: true,
		},{
			title: 'Bugzilla',
			field: 'Bznumber',
		},{
			title: 'Comment',
			field: 'Comment',
		},{
			title: 'Operation',
			field: 'operate',
			align: 'center',
			events: operateEvents,
			formatter: operateFormatter
		}
		]
	});
}

function operateFormatter(value, row, index){
	return ['<a class="Edit" href="javascript:void(0)" title="Edit">',
		'<i class="glyphicon glyphicon-pencil"></i>',
		'</a> '].join('');
}

window.operateEvents = {
	'click .Edit': function(e, value, row, index){
		localStorage.setItem('editLogId',row.Id);
		$.ajax({
			url : '/getLogById',
			data : {logid: row.Id},
			type : 'POST',
			success: function(res){
				var data = JSON.parse(res);
				$('#showInfo').val(data[0]['Information']);
				$('#editComment').val(data[0]['Comment']);
				$('#bznumber').val(data[0]['Bznumber']);
				$('#editModal').modal();
			},
			error: function(error){
				alert(error);
			}
		});
	},
};

function detailFormatter(index, row){
	var html = [];
	var tags = "";
	localStorage.setItem('tagLogId',row.Id);
	$.ajax({
		url : '/getTagById',
		data : {tagLogId: row.Id},
		type : 'POST',
		async: false,
		success: function(res){
			var data = JSON.parse(res);
			console.log(data);
			for(var p in data){
				tags = tags + data[p].Platform + ' with ' + data[p].OS + data[p].Phase + '; ';
			}
			html.push('<p><strong>Detail Information: </strong>' + tags + '</p>');
		},
		error: function(error){
			alert(error);
		}
	});
	return html.join('');
}


function initlistTableAction(){
	$('#listTable').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#confirmDelete').prop('disabled', !$('#listTable').bootstrapTable('getSelections').length);
				selections = getIdSelections("#listTable");
	});
}

function initbtnconfirmDeleteAction(){
	$('#confirmDelete').click(function(){
		var ids = getIdSelections("#listTable");
		localStorage.setItem('deleteLogId',ids);
		$('#deleteModal').modal();
	});
}

function initbtnDeleteAction(){
    $('#btnDelete').click(function(){
        $.ajax({
            url : '/deleteLog',
            data : {logids:localStorage.getItem('deleteLogId')},
            type : 'POST',
            success: function(res){
                $('#listTable').bootstrapTable('destroy');
                var result = JSON.parse(res);
                if(result.status == 'OK'){
                    $('#deleteModal').modal('hide');
                    $('#confirmDelete').prop('disabled', true);
                    GetDataFromDB();
                }
                else{
                    alert(result.status);
                }
            },
            error: function(error){
                console.log(error);
            }
        });
    });
}

function initbtnUpdateAction(){
    $('#btnUpdate').click(function(){
        $.ajax({
            url : '/updateLog',
            data : {comment:$('#editComment').val(),stat:$('#editStatus').val(),bznumber:$('#bznumber').val(),logid:localStorage.getItem('editLogId')},
            type : 'POST',
            success: function(res){
                $('#editModal').modal('hide');
                $('#listTable').bootstrapTable('destroy');
                GetDataFromDB();
            },
            error: function(error){
                console.log(error);
            }
        });
    });
}

function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnDeleteAction();
    initbtnUpdateAction();
}