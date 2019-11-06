
function GetDataFromDB(){
	$.ajax({
		url : '/getOSImages',
		type : 'GET',
		success: function(res){
			var recordObj = JSON.parse(res);
			$('#listTableISO').bootstrapTable({
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
					title: 'VENDER',
					field: 'Vender',
					sortable: true,
				},{
					title: 'VERSION',
					field: 'Version',
				},{
					title: 'PHASE',
					field: 'Phase',
				},{
					title: 'ImgNAME',
					field: 'Imgname',
				},{
					title: 'MD5',
					field: 'MD5',
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
	$('#listTableISO').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#btnconfirmDeleteISO').prop('disabled', !$('#listTableISO').bootstrapTable('getSelections').length);
				selections = getIdSelections('#listTableISO');
				console.log(selections);
	});
}

function initbtnconfirmDeleteAction(){
	$('#btnconfirmDeleteISO').click(function(){
		var ids = getIdSelections('#listTableISO');
		localStorage.setItem('deleteISOId',ids);
		$('#deleteModal').modal();
	});
}
function initbtnshowUploadAction(){
	$('#btnshowUploadCF').click(function(){;
		$('#uploadModal').modal();
	});
}
function initbtnshowAddAction(){
	$('#btnshowAddISO').click(function(){;
		$('#inputModal').modal();
	});
}
function initbtnAddAction(){
		$('#btnAddISO').click(function(){
			var postData = {Vender:$('#inputVender').val(),
			                Version:$('#inputVersion').val(),
			                Phase:$('#inputPhase').val(),
			                ISO:$('#inputISO').val(),
			                MD5:$('#inputMD5').val()}
			$('#listTableISO').bootstrapTable('destroy');
			$.ajax({
				url : '/addOSImage',
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
				url : '/deleteISOImages',
				data : {ISOIds:localStorage.getItem('deleteISOId')},
				type : 'POST',
				success: function(res){
					$('#listTableISO').bootstrapTable('destroy');
					var result = JSON.parse(res);
					if(result.status == 'OK'){
						$('#deleteModal').modal('hide');
						$('#btnconfirmDeleteISO').prop('disabled', true);
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
    $("#uploadCF").fileinput({
        uploadUrl: "/uploadOSCF",
        allowedFileExtensions : ['xml', 'cfg', 'iso'],
        maxFileCount: 50,
        maxFileSize:0,
        enctype: 'multipart/form-data',
        showUpload: true,
        browseClass: "btn btn-primary",
    });

    //Temporarily useless
    $("#uploadCF").on("fileuploaded", function (event, data, previewId, index) {
//        $("#uploadModal").modal("hide");
    });
}


function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnshowUploadAction();
    initbtnshowAddAction();
    initbtnAddAction();
    initbtnDeleteAction();
    inituploadAction();
}

