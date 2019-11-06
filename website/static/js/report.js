function GetDataFromDB(){
    GetReports();
}

function initButtonsAction(){

}

function GetReports(){
	var style = "";
	var vercount = 0;
	var count = 0;
	var classes = ['active', 'success', 'info', 'warning', 'danger'];
	$.ajax({
		url : '/getReport',
		type : 'GET',
		success: function(res){
			var data = JSON.parse(res);
			var element_sles = document.getElementById("sles");
			var element_rhel = document.getElementById("rhel");
			var element_vmware = document.getElementById("vmware");
			var divrhel = document.createElement("div");
			var divsles = document.createElement("div");
			var divvmware = document.createElement("div");
			for(var p in data){
			    for(var ver in data[p]){
                                var tags = "";
				var panel = document.createElement("div");
				panel.className = "panel panel-info";
				var panelhead = document.createElement("div");
				panelhead.className = "panel-heading";
				var paneltitle = "<h3 class='panel-title' data-toggle='collapse' href='#" + vercount + "'> " + p + " " + ver + "</h3>";
				panelhead.innerHTML = paneltitle;
				panel.appendChild(panelhead);
				var panelbody = document.createElement("div");
				panelbody.className = "panel-body";
				var demo = document.createElement("div");
				demo.className = "collapse";
				demo.setAttribute("id", vercount); 
				vercount = vercount + 1;
				for(var i in data[p][ver]){
				    item = data[p][ver][i];
				    count = count + 1;
				    style = classes[count%5];
				    tags = tags + " <button id='btnReport" + count + "' class='btn btn-" + style + "' onclick='btnfunc(this)' name=" + item.OSId + " ><i class='glyphicon glyphicon-book'></i> " + item.OS + item.Version + "-" + item.Phase + "</button> ";
				}
				demo.innerHTML = tags;
				panelbody.appendChild(demo);
				panel.appendChild(panelbody);
				if(p == "RHEL" && !jQuery.isEmptyObject(data[p])){
				    element_rhel.appendChild(panel);
				}
				if(p == "SLES" && !jQuery.isEmptyObject(data[p])){
				    element_sles.appendChild(panel);
				}
				if(p == "VMware" && !jQuery.isEmptyObject(data[p])){
				    element_vmware.appendChild(panel);
				}
			    }
			}
		},
		error: function(error){
			alert(error);
		}
	});
}

function btnfunc(ele){
	$('#tableReport').bootstrapTable('destroy');
	$.ajax({
		url : '/getReportByConfig',
		data: {osid: ele.name},
		type: 'POST',
		success: function(res){
			var recordObj = JSON.parse(res);
            $('#tableReport').bootstrapTable({
                data: recordObj,
                columns : [{
                    title: 'TaskID',
                    field: 'TaskId',
                    sortable: true,
                },{
                    title: 'ID',
                    field: 'OSId',
                    sortable: true,
                    visible: false,
                },{
                    title: 'Platform',
                    field: 'Platform',
                    sortable: true,
                },{
                    title: 'Date',
                    field: 'Date',
                    sortable: true
                },{
                    title: 'Type',
                    field: 'Type',
                    sortable: true
                },{
                    title: 'Operation',
                    field: 'operate',
                    align: 'center',
                    events: operateEvents,
                    formatter: operateFormatter
                }
                ]
            });
			},
		error: function(error){
			alert(error);
		}
	});

	$('#modalReport').modal();
}


function operateFormatter(value, row, index){
    if(row.Type == "pci"){
	return ['<a class="Download" href="javascript:void(0)" title="Download">',
		'<i class="glyphicon glyphicon-download"></i>',
		'</a> '].join('');
    }else if(row.Type == "report"){
	return ['<a class="Download" href="javascript:void(0)" title="Download">',
		'<i class="glyphicon glyphicon-download"></i>',
		'</a> '].join('');
    }else{
	console.log("Wrong type");
    }
}

window.operateEvents = {
	'click .Download': function(e, value, row, index){
		$.ajax({
			url : '/getFileById',
			data : {idtype: row.TaskId+','+row.OSId+','+row.Type},
			type : 'POST',
			success: function(res){
				var data = JSON.parse(res);
				if(row.Type=="pci"){
				    console.log("pciid file is " + data[0].pcidir + ".xlsx" )
					location.href = data[0].pcidir + ".xlsx"
				}else if(row.Type=="report"){
				    console.log("report file is " + data[0].logdir + "/report_" + data[0].time + ".xlsx")
					location.href = data[0].logdir + "/report_" + data[0].time + ".xlsx"
				}else{
					console.log("Wrong download link!")
				}
			},
			error: function(error){
				console.log(error);
			},
		});
	},
};



