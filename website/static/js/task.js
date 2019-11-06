var recordControlServer;
var recordTestCase;
var recordOSImage;
var recordRHOSImg;
var recordSSOSImg;
var recordVMOSImg;
var recordWinOSImg;
var recordRPM;
var checkedIDFeature;
var checkedIDInbox;


function GetTaskList(){
	$.ajax({
		url : '/getTasks',
		type : 'GET',
		success: function(res){
			var recordObj = JSON.parse(res);
			$('#listTableTask').bootstrapTable({
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
					title: 'Task type',
					field: 'TaskType',
					sortable: true,
				},{
					title: 'Tester',
					field: 'TesterName',
					sortable: true,
				},{
					title: 'Control Server',
					field: 'CrlServer',
					sortable: true,
				},{
					title: 'SUT MAC',
					field: 'SutMAC',
				},{
					title: 'MTSN',
					field: 'MTSN',
				},{
					title: 'OS version',
					field: 'OSVersion',
				},{
					title: 'OS image',
					field: 'OSImage',
				},{
					title: 'Kernel PKG',
					field: 'kernelPKG',
				},{
				    title: 'Status',
				    field: 'Status',
				    formatter: statusFormatter,
				},{
					title: 'CFG View',
					field: 'operate',
					align: 'center',
					events: operateEvents,
					formatter: operateFormatter,
				}
				]
			});
		},
		error: function(error){
			alert(error);
		}
	});
}

function statusFormatter(value, row, index){
    var value="";
    if(row.Status==0){
        value = "ongoing";
    }else if(row.Status==1){
		value = "completed";
	}else if(row.Status==-1){
	    value = "failed";
	}
	        return value;
}

function operateFormatter(value, row, index){
	return ['<a class="Edit" href="javascript:void(0)" title="Edit">',
		'<i class="glyphicon glyphicon glyphicon-file"></i>',
		'</a> '].join('');
}

window.operateEvents = {
	'click .Edit': function(e, value, row, index){
		$.ajax({
			url : '/getConfigById',
			data : {taskid: row.Id},
			type : 'POST',
			success: function(res){
			    var data = JSON.parse(res);
			    var String = "";
			    var lineNumb = 0;
                $('#configName').text(data[0]['fileName']);
                $("#showDes").empty();
                var fileContent = data[0]['content'];
                for (var item in fileContent){
                    String=String + fileContent[item]
                    lineNumb++
                }
                $("#showDes").text(String);
                $("#showDes").attr("rows",lineNumb)
				$('#viewModal').modal();
			},
			error: function(error){
				alert(error);
			}
		});
	},
};
/**
 * Insert the following html into the <select ...... id="inputControlServer" ......>
 * <option>BDC_1</option>
 * <option>TDC_2</option>
 *  ......
 */
function GetControlServers(){
	$.ajax({
		url : '/getControlServers',
		type : 'GET',
		success: function(res){
			recordControlServer = JSON.parse(res);
			$("#inputControlServer").empty();
            for (var item in recordControlServer){
                var optionString=$("<option></option>").text(recordControlServer[item].Location+"_"+recordControlServer[item].Id)
                $("#inputControlServer").append(optionString);
            }
            $('#inputControlServer').selectpicker('render');
            $('#inputControlServer').selectpicker('refresh');
		},
		error: function(error){
			alert(error);
		}
	});

}

function insertFeature(record, inputname, divID){
    var i = 1;
    for (var item in record){
        var labelString=$("<label></label>").attr({"class" : "checkbox-inline col-xs-5"})
                                              .append("<input type='checkbox' name="+ inputname + " value='"+record[item].Id+"'/>"+record[item].Name);
        if(i%2 != 0){
            var divString=$("<div></div>").append(labelString);
            $(divID).append(divString);
        }else{
            $(divID).children().last().append(labelString);
        }
        i++;
    }
}

function insertInbox(record, inputname, divID){
    //recordTCInbox contains only one item
    for (var Inbox in record){
        var labelString=$("<label></label>").attr({"class" : "checkbox-inline col-xs-5"})
                                              .append("<input type='checkbox' name=" + inputname +" value='"+record[Inbox].Id+"'/>"+record[Inbox].Name);
        var divString=$("<div></div>").append(labelString);
        $(divID).append(divString);
    }
}


/**
 * Insert the following html into the <div id="testCaseList" class="panel-body">
 * Two labels per div
 * <div>
 *     <label class="checkbox-inline col-xs-5">
 *        <input type="checkbox"  value=item.Id> item.Name
 *     </label>
 * </div>
 */
function GetTestCases(){
	$.ajax({
		url : '/getTestCases',
		type : 'GET',
		success: function(res){
			recordTestCase = JSON.parse(res);
            var platform;
            var recordTCFeatureRH=new Array();
            var recordTCFeatureSS=new Array();
            var recordTCFeatureWin=new Array();
            var recordTCFeatureVM=new Array();
            var recordTCInboxL=new Array();
            var recordTCInboxV=new Array();
            var recordTCInboxW=new Array();
            for (var item in recordTestCase){
                if(recordTestCase[item].Name.toLowerCase() == "linux_inbox"){
                    recordTCInboxL.push(recordTestCase[item]);
                }else if(recordTestCase[item].Name.toLowerCase() == "vmware_inbox"){
                    recordTCInboxV.push(recordTestCase[item]);
                }else if(recordTestCase[item].Name.toLowerCase() == "windows_inbox"){
                    recordTCInboxW.push(recordTestCase[item]);
                }else if (recordTestCase[item].Name.indexOf("_inbox") == "-1"){
                    platform = recordTestCase[item].Platform.split(",");
                    for (var pf in platform){
                        if (platform[pf] == "RedHat"){
                            recordTCFeatureRH.push(recordTestCase[item]);
                        }else if(platform[pf] == "SUSE"){
                            recordTCFeatureSS.push(recordTestCase[item]);
                        }else if(platform[pf] == "VMware"){
                            recordTCFeatureVM.push(recordTestCase[item]);
                        }else if(platform[pf] == "Windows"){
                            recordTCFeatureWin.push(recordTestCase[item]);
                        }
                    }
                }
            }
            $("#tcListForFeatureRH").empty();
            $('#tcListForFeatureSS').empty();
            $('#tcListForFeatureWin').empty();
            $('#tcListForFeatureVM').empty();

            insertFeature(recordTCFeatureRH,"FeatureForRH", "#tcListForFeatureRH");
            insertFeature(recordTCFeatureSS,"FeatureForSS", "#tcListForFeatureSS");
            insertFeature(recordTCFeatureWin,"FeatureForWin", "#tcListForFeatureWin");
            insertFeature(recordTCFeatureVM,"FeatureForVM", "#tcListForFeatureVM");

            //testcase group need to hide :TBD???

		},
		error: function(error){
			alert(error);
		}
	});
}

/**
 * Insert the following html into the <select ...... id="inputOSImage" ......>
 * <option>isoname1</option>
 * <option>isoname2</option>
 *  ......
 */
function GetOSImages(){
	$.ajax({
		url : '/getOSImages',
		type : 'GET',
		success: function(res){
			var imageName;
			var optionString;
			recordOSImage = JSON.parse(res);

			recordRHOSImg = [];
			recordSSOSImg = [];
			recordVMOSImg = [];
			recordWinOSImg = [];
			recordRPM = [];

			for (var item in recordOSImage){
			    imageName = recordOSImage[item].Imgname;
			    if (imageName.indexOf(".iso") != "-1" && imageName.toLowerCase().indexOf("rhel-")==0){
			        recordRHOSImg.push(recordOSImage[item]);
			    }else if (imageName.indexOf(".iso") != "-1" && imageName.toLowerCase().indexOf("sle-")==0){
			        recordSSOSImg.push(recordOSImage[item]);
			    }else if (imageName.indexOf(".iso") != "-1" && imageName.toLowerCase().indexOf("vmware")==0){
			        recordVMOSImg.push(recordOSImage[item]);
			    }else if (imageName.indexOf(".iso") != "-1" && imageName.toLowerCase().indexOf("windows")!="-1"){
			        recordWinOSImg.push(recordOSImage[item]);
			    }else if (imageName.indexOf(".rpm") != "-1"){
			        recordRPM.push(recordOSImage[item]);
			    }
			}
			changeISO();

			$("#inputKernelRPM").empty();
            for(var item in recordRPM){
                imageName = recordRPM[item].Imgname;
                optionString=$("<option></option>").text(imageName)
                $("#inputKernelRPM").append(optionString);
            }
            $('#inputKernelRPM').selectpicker('render');
            $('#inputKernelRPM').selectpicker('refresh');
		},
		error: function(error){
			alert(error);
		}
	});
}

function changeTestcase(){
    var isoName;
    var isoNameLowCase;
    $('#tcListForFeatureRH').hide();
    $('#tcListForFeatureSS').hide();
    $('#tcListForFeatureWin').hide();
    $('#tcListForFeatureVM').hide();

    targetOS = $('#inputTagetOS').val();
    if($('#inputTaskType').val()=="Feature test"){
//        isoName = $('#inputOSImage').val();
//        isoName += '';
//        isoNameLowCase = isoName.toLowerCase();
        if(targetOS == 'RedHat'){
            $("#tcListForFeatureRH").show();
        }else if(targetOS == 'SUSE'){
            $('#tcListForFeatureSS').show();
        }else if(targetOS == 'VMware'){
            $('#tcListForFeatureVM').show();
        }else if(targetOS == 'Windows'){
            $('#tcListForFeatureWin').show();
        }
    }
}

function changeISO(){
			$("#inputOSImage").empty();
			targetOS = $("#inputTagetOS").val();
			if (targetOS == "RedHat"){
			    for(var item in recordRHOSImg){
			        imageName = recordRHOSImg[item].Imgname;
			        optionString=$("<option></option>").text(imageName)
                    $("#inputOSImage").append(optionString);
			    }
			}else if (targetOS == "SUSE"){
			    for(var item in recordSSOSImg){
			        imageName = recordSSOSImg[item].Imgname;
			        optionString=$("<option></option>").text(imageName)
                    $("#inputOSImage").append(optionString);
			    }
			}else if (targetOS == "VMware"){
			    for(var item in recordVMOSImg){
			        imageName = recordVMOSImg[item].Imgname;
			        optionString=$("<option></option>").text(imageName)
                    $("#inputOSImage").append(optionString);
			    }
			}else if (targetOS == "Windows"){
				for(var item in recordWinOSImg){
			        imageName = recordWinOSImg[item].Imgname;
			        optionString=$("<option></option>").text(imageName)
                    $("#inputOSImage").append(optionString);
			    }
			}
            $('#inputOSImage').selectpicker('render');
            $('#inputOSImage').selectpicker('refresh');
}

function inituploadAction(){
    $("#uploadPCIID").fileinput({
        uploadUrl: "/uploadPCIID",
        allowedFileExtensions : ['xlsx', 'xls','txt'],
        maxFileCount: 50,
        maxFileSize:0,
        enctype: 'multipart/form-data',
        showUpload: true,
        browseClass: "btn btn-primary",
    });

    //Temporarily useless
    $("#uploadPCIID").on("fileuploaded", function (event, data, previewId, index) {
//        console.log("for debug fileuploaded")
//        $.ajax({
//            url : '/getDeviceAfterUpload',
//            type : 'GET',
//            success: function(res){
//                display(res)
//            },
//            error: function(error){
//                alert(error);
//            }
//        });
//        $("#uploadPCIID").modal("hide");
    });
}


function ChangeDisplay(){
    targetOS = $("#inputTagetOS").val();
    if($('#inputTaskType').val()=="OS deployment"){
        $('#TeskCaseGroup').hide();
        $('#rpmGroup').hide();
        $('#SUTGroup').show();
    }else if($('#inputTaskType').val()=="Feature test"){
        $('#TeskCaseGroup').show();
        $('#rpmGroup').hide();
        $('#SUTGroup').show();
    }else{
        $('#TeskCaseGroup').hide();
        $('#SUTGroup').hide();
        if(targetOS == "RedHat" || targetOS == "SUSE"){
            $('#rpmGroup').show();
        }else if(targetOS == "VMware"){
            $('#rpmGroup').hide();
        }
    }
    changeTestcase();
    changeISO();
}

function initlistTableAction(){
	$('#listTableTask').on('check.bs.table uncheck.bs.table ' +
			'check-all.bs.table uncheck-all.bs.table', function(){
				$('#btnconfirmDeleteTask').prop('disabled', !$('#listTableTask').bootstrapTable('getSelections').length);
				selections = getIdSelections('#listTableTask');
				console.log(selections);
	});
}
function initbtnconfirmDeleteAction(){
	$('#btnconfirmDeleteTask').click(function(){
		var ids = getIdSelections('#listTableTask');
		localStorage.setItem('deleteTaskId',ids);
		$('#deleteModal').modal();
	});
}
function initbtnshowAddAction(){
	$('#btnshowAddTask').click(function(){;
		$('#inputModal').modal();
	});
}

//from crtServer and recordControlServer;
function getIPFromCtl(controlServerName){
    var IPofCtlServer = {publicIP:"",
                         privateIP:""}
    if (controlServerName!=""){
        var part = controlServerName.split("_")
        selectedId = part[part.length-1]
    }else{
        selectedId = -1
    }

    for (var item in recordControlServer){
        if(recordControlServer[item].Id == selectedId){
            IPofCtlServer.publicIP=recordControlServer[item].PubIp
            IPofCtlServer.privateIP=recordControlServer[item].PriIp
        }
    }
    return IPofCtlServer
}

//from check box value and recordTestCase;
function getScrFromCkbox(){
    scriptList = ""
    IDList = getcheboxStatus();

    for (var ID in IDList){
        for (var item in recordTestCase){
            if(recordTestCase[item].Id == IDList[ID]){
                if (scriptList == ""){
                    scriptList = recordTestCase[item].Description
                }else{
                    scriptList = scriptList + "," + recordTestCase[item].Description
                }
            }
        }
    }
    return scriptList
}

function initbtnAddAction(){
		$('#btnAddTask').click(function(){
            var IPofCtlServer = getIPFromCtl($('#inputControlServer').val())
			var postData
			var script
			targetOS = $("#inputTagetOS").val();
			if($('#inputTaskType').val() == "Feature test"){
			    script = getScrFromCkbox();
			    if($('#inputMTSN').val() == '' || $('#inputSUTMAC').val() == '' || script == ''){
			        alert("Test Case,SUT MAC and MTSN must be set!");
			        return
			    }
			    postData = {taskType:$('#inputTaskType').val(),
			                crlServer:$('#inputControlServer').val(),
			                OSImage:$('#inputOSImage').val(),
			                kernelPKG:"",
			                sutMACaddress:$('#inputSUTMAC').val(),
			                MTSN:$('#inputMTSN').val(),
			                testerName:$('#userName').text().replace(/\t/g, "").replace(/\n/g, ""),
			                PubIPAddress:IPofCtlServer.publicIP,
			                PriIPAddress:IPofCtlServer.privateIP,
			                scriptList:script}
			}else if($('#inputTaskType').val() == "Inbox test"){
			    script = ""
			    if ($('#inputTagetOS').val() == "VMware"){
			        postData = {taskType:$('#inputTaskType').val(),
			                crlServer:$('#inputControlServer').val(),
			                OSImage:$('#inputOSImage').val(),
			                kernelPKG:"",
			                sutMACaddress:"",
			                MTSN:"",
			                status:0,
			                testerName:$('#userName').text().replace(/\t/g, "").replace(/\n/g, ""),
			                PubIPAddress:IPofCtlServer.publicIP,
			                PriIPAddress:IPofCtlServer.privateIP,
			                scriptList:script}
			    }else {
			        postData = {taskType:$('#inputTaskType').val(),
			                crlServer:$('#inputControlServer').val(),
			                OSImage:$('#inputOSImage').val(),
			                kernelPKG:$('#inputKernelRPM').val(),
			                sutMACaddress:"",
			                MTSN:"",
			                status:0,
			                testerName:$('#userName').text().replace(/\t/g, "").replace(/\n/g, ""),
			                PubIPAddress:IPofCtlServer.publicIP,
			                PriIPAddress:IPofCtlServer.privateIP,
			                scriptList:script}
			    }
			}else if($('#inputTaskType').val() == "OS deployment"){
				if($('#inputMTSN').val() == '' || $('#inputSUTMAC').val() == ''){
			        alert("SUT MAC and MTSN must be set!");
			        return
			    }
			    postData = {taskType:$('#inputTaskType').val(),
			                crlServer:$('#inputControlServer').val(),
			                OSImage:$('#inputOSImage').val(),
			                kernelPKG:"",
			                sutMACaddress:$('#inputSUTMAC').val(),
			                MTSN:$('#inputMTSN').val(),
			                status:0,
			                testerName:$('#userName').text().replace(/\t/g, "").replace(/\n/g, ""),
			                PubIPAddress:IPofCtlServer.publicIP,
			                PriIPAddress:IPofCtlServer.privateIP,
			                scriptList:""}
			}
			$.ajax({
				url : '/addTask',
				data : postData,
				type : 'POST',
				success: function(res){
					result = JSON.parse(res);
					console.log(result);
					if(result.status == "NG" && result.detail.indexOf("need PCIID file") != -1){
					    if(targetOS == "RedHat" || targetOS == "SUSE"){
					        document.getElementById("uploadLabel").innerHTML = "Upload your PCIID";
					        $('#uploadModal').modal("show");
					    }else if(targetOS == "VMware"){
					        document.getElementById("uploadLabel").innerHTML = "Upload your PCIID and Driver File";
					        $('#uploadModal').modal("show");
					    }
					}else if (result.status == "OK") {
					    $('#listTableTask').bootstrapTable('destroy');
					    $('#inputModal').modal('hide');
					    GetDataFromDB();
					    initbtnAddAction();
					}
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
				url : '/deleteTasks',
				data : {TaskIds:localStorage.getItem('deleteTaskId')},
				type : 'POST',
				success: function(res){
					$('#listTableTask').bootstrapTable('destroy');
					var result = JSON.parse(res);
					if(result.status == 'OK'){
						$('#deleteModal').modal('hide');
						$('#btnconfirmDeleteTask').prop('disabled', true);
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

function initbtnTaskType(){
	$('#inputTaskType').change(function(){
	    ChangeDisplay();
	});
}

function initbtnTargetOS(){
    $('#inputTagetOS').change(function(){
	    ChangeDisplay();
	});
}
function getcheboxStatus(){
    checkedID=[]

   if($("#tcListForFeatureRH").is(':visible')){
       $('input[name="FeatureForRH"]:checked').each(function(i){
            checkedID.push($(this).val());
       });
       return checkedID
   }else if($("#tcListForFeatureSS").is(':visible')){
       $('input[name="FeatureForSS"]:checked').each(function(i){
            checkedID.push($(this).val());
       });
       return checkedID
   }else if($("#tcListForFeatureWin").is(':visible')){
       $('input[name="FeatureForWin"]:checked').each(function(i){
            checkedID.push($(this).val());
       });
       return checkedID
   }else if($("#tcListForFeatureVM").is(':visible')){
       $('input[name="FeatureForVM"]:checked').each(function(i){
            checkedID.push($(this).val());
       });
       return checkedID
   }
}



function GetDataFromDB(){
       GetTaskList();
       GetControlServers();
       GetTestCases();
       GetOSImages();
       ChangeDisplay();
}

function initButtonsAction(){
    initlistTableAction();
    initbtnconfirmDeleteAction();
    initbtnshowAddAction();
    initbtnAddAction();
    initbtnDeleteAction();
    initbtnTaskType();
    initbtnTargetOS();
	inituploadAction();
}
