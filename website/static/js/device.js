function GetDevices(){
	$.ajax({
		url : '/getDevice',
		type : 'GET',
		success: function(res){
			display(res)
		},
		error: function(error){
			alert(error);
		}
	});
}

function display(res){
	var recordObj = JSON.parse(res);
	$('#listTable').bootstrapTable({
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
					title: 'Vendor',
					field: 'Vendor',
					sortable: true,
				},{
					title: 'Description',
					field: 'Description',
				},{
					title: 'Vendorid',
					field: 'Vendorid',
				},{
					title: 'Deviceid',
					field: 'Deviceid',
				},{
					title: 'SubVendorid',
					field: 'Subvendorid',
				},{
					title: 'SubDeviceid',
					field: 'Subdeviceid',
				},{
				    	title: 'Driver',
					field: 'Driver',
				},{
				    	title: 'Version',
					field: 'Version',
				},{
					title: 'Status',
					field: 'Status',
					sortable: true,
				},{
					title: 'Project',
					field: 'Project',
					sortable: true,
//				},{
//					title: 'Operation',
//					field: 'operate',
//					align: 'center',
//					events: operateEvents,
//					formatter: operateFormatter
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
		localStorage.setItem('editDeviceId',row.Id);
		$.ajax({
			url : '/getDeviceById',
			data : {pciidid: row.Id},
			type : 'POST',
			success: function(res){
				var data = JSON.parse(res);
				$('#showDes').val(data[0]['Description']);
				$('#editVendor').val(data[0]['Vendorid']);
				$('#editDevice').val(data[0]['Deviceid']);
				$('#editSubvendor').val(data[0]['Subvendorid']);
				$('#editSubdevice').val(data[0]['Subdeviceid']);
				$('#editPro').val(data[0]['Project']);
				$('#editModal').modal();
			},
			error: function(error){
				alert(error);
			}
		});
	},
};

//function initbtnshowUploadAction(){
//	$('#btnshowUploadPCIID').click(function(){;
//		$('#uploadModal').modal();
//	});
//}

//function inituploadAction(){
//    $("#uploadPCIID").fileinput({
//        uploadUrl: "/uploadPCIID",
//        allowedFileExtensions : ['xlsx', 'xls'],
//        maxFileCount: 50,
//        maxFileSize:0,
//        enctype: 'multipart/form-data',
//        showUpload: true,
//        browseClass: "btn btn-primary",
//    });
//
//    //Temporarily useless
//    $("#uploadPCIID").on("fileuploaded", function (event, data, previewId, index) {
////        console.log("for debug fileuploaded")
////        $.ajax({
////            url : '/getDeviceAfterUpload',
////            type : 'GET',
////            success: function(res){
////                display(res)
////            },
////            error: function(error){
////                alert(error);
////            }
////        });
////        $("#uploadModal").modal("hide");
//    });
//}


function initlistTableAction(){
	$('#listTable').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#confirmDelete').prop('disabled', !$('#listTable').bootstrapTable('getSelections').length);
				selections = getIdSelections('#listTable');
				console.log(selections);
	});
}

function initbtnconfirmDeleteAction(){
	$('#confirmDelete').click(function(){
		var ids = getIdSelections('#listTable');
		localStorage.setItem('deleteDeviceId',ids);
		$('#deleteModal').modal();
	});
}

function initbtnUpdateAction(){
    $('#btnUpdate').click(function(){
        $('#listTable').bootstrapTable('destroy');
        $.ajax({
            url : '/updateDevice',
            data : {inputPro:$('#editPro').val(),vendorid:$('#editVendor').val(),deviceid:$('#editDevice').val(),subvendorid:$('#editSubvendor').val(),subdeviceid:$('#editSubdevice').val(),inputStat:$('#editStatus').val(),pciidid:localStorage.getItem('editDeviceId')},
            type : 'POST',
            success: function(res){
                $('#editModal').modal('hide');
                GetDevices();
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
            url : '/deleteDevice',
            data : {pciidids:localStorage.getItem('deleteDeviceId')},
            type : 'POST',
            success: function(res){
                $('#listTable').bootstrapTable('destroy');
                var result = JSON.parse(res);
                if(result.status == 'OK'){
                    $('#deleteModal').modal('hide');
                    $('#confirmDelete').prop('disabled', true);
                    GetDevices();
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
    GetDevices();
}

function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnUpdateAction();
    initbtnDeleteAction();
//    initbtnAddAction();
//    initbtnshowUploadAction();
//    initbtnshowAddAction();
//    inituploadAction();
}


