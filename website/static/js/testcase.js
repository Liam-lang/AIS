
function GetDataFromDB(){
	$.ajax({
		url : '/getTestCases',
		type : 'GET',
		success: function(res){
			var recordObj = JSON.parse(res);
			$('#listTableTC').bootstrapTable({
				data: recordObj,
				columns : [{
					field: 'state',
					checkbox: true,
					align: 'center',
					valign: 'middle',
				},{
					title: 'ID',
					field: 'Id',
				},{
					title: 'CASE NAME',
					field: 'Name',
				},{
					title: 'SCRIPT NAME',
					field: 'Description',
				},{
				 	title: 'PLATFORM',
					field: 'Platform',
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
	$('#listTableTC').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#btnconfirmDeleteTC').prop('disabled', !$('#listTableTC').bootstrapTable('getSelections').length);
				selections = getIdSelections('#listTableTC');
				console.log(selections);
	});
}

function initbtnconfirmDeleteAction(){
	$('#btnconfirmDeleteTC').click(function(){
		var ids = getIdSelections('#listTableTC');
		localStorage.setItem('deleteTCId',ids);
		$('#deleteModal').modal();
	});
}
function initbtnshowAddAction(){
	$('#btnshowAddTC').click(function(){;
		$('#inputModal').modal();
	});
}

function initbtnshowUploadAction(){
	$('#btnshowUploadTC').click(function(){;
		$('#uploadModal').modal();
	});
}

function getPlatform(){
   Platform=""
   $('input[name="Platform"]:checked').each(function(i){
        if(Platform == ""){
            Platform = $(this).val()
        }else{
            Platform = Platform + ","+$(this).val()
        }
   });
   return Platform
}
function initbtnAddAction(){
		$('#btnAddTC').click(function(){
		    var platformList = getPlatform();
			var postData = {Name:$('#inputName').val(),
			                Description:$('#txtDes').val(),
			                Platform:platformList}
			$('#listTableTC').bootstrapTable('destroy');
			$.ajax({
				url : '/addTestCase',
				data : postData,
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
				url : '/deleteTestCases',
				data : {TCIds:localStorage.getItem('deleteTCId')},
				type : 'POST',
				success: function(res){
					$('#listTableTC').bootstrapTable('destroy');
					var result = JSON.parse(res);
					if(result.status == 'OK'){
						$('#deleteModal').modal('hide');
						$('#btnconfirmDeleteTC').prop('disabled', true);
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

function inituploadAction(){
    $("#uploadTC").fileinput({
        uploadUrl: "/uploadTestCase",
        allowedFileExtensions : ['py', 'sh'],
        maxFileCount: 50,
        enctype: 'multipart/form-data',
        showUpload: true,
        browseClass: "btn btn-primary",
    });

    //Temporarily useless
    $("#uploadTC").on("fileuploaded", function (event, data, previewId, index) {
//        $("#uploadModal").modal("hide");
    });
}

function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnshowAddAction();
    initbtnAddAction();
    initbtnDeleteAction();
    initbtnshowUploadAction();
    inituploadAction();
}
