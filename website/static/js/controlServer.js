
function GetControlServers(){
	$.ajax({
		url : '/getControlServers',
		type : 'GET',
		success: function(res){
			var recordObj = JSON.parse(res);
			$('#listTableCS').bootstrapTable({
				data: recordObj,
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
					title: 'NAME',
					field: 'Name',
				},{
					title: 'Public IP',
					field: 'PubIp',
				},{
					title: 'Private IP',
					field: 'PriIp',
				},{
					title: 'MAC',
					field: 'MAC',
				},{
					title: 'Location',
					field: 'Location',
					sortable: true,
				}
				]
			});
		},
		error: function(error){
			alert(error);
		}
	});
}

function initlistTableAction(){
	$('#listTableCS').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#btnconfirmDeleteCS').prop('disabled', !$('#listTableCS').bootstrapTable('getSelections').length);
				selections = getIdSelections('#listTableCS');
				console.log(selections);
	});
}

function initbtnconfirmDeleteAction(){
	$('#btnconfirmDeleteCS').click(function(){
		var ids = getIdSelections('#listTableCS');
		localStorage.setItem('deleteCSId',ids);
		$('#deleteModal').modal();
	});
}
function initbtnshowAddAction(){
	$('#btnshowAddCS').click(function(){;
		$('#inputModal').modal();
	});
}
function initbtnAddAction(){
		$('#btnAddCS').click(function(){
			$('#listTableCS').bootstrapTable('destroy');
			$.ajax({
				url : '/addControlSever',
				data : {Name:$('#inputName').val(),PubIP:$('#inputPubIP').val(),PriIP:$('#inputPriIP').val(),MAC:$('#inputMAC').val(),Location:$('#inputLocation').val()},
				type : 'POST',
				success: function(res){
					$('#inputModal').modal('hide');
					GetDataFromDB();
				},
				error: function(error){
					console.log(error);
				}
			});
		});
}
function initbtnDeleteAction(){
		$('#btnDelete').click(function(){
			$.ajax({
				url : '/deleteControlServers',
				data : {CSIds:localStorage.getItem('deleteCSId')},
				type : 'POST',
				success: function(res){
					$('#listTableCS').bootstrapTable('destroy');
					var result = JSON.parse(res);
					if(result.status == 'OK'){
						$('#deleteModal').modal('hide');
						$('#btnconfirmDeleteCS').prop('disabled', true);
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

function GetDataFromDB(){
    GetControlServers();
}

function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnshowAddAction();
    initbtnAddAction();
    initbtnDeleteAction();
}
