

function getIdSelections(listTable){
	return $.map($(listTable).bootstrapTable('getSelections'), function(row){
		return row.Id
	});
}

function rowStyle(row, index){
	var classes = ['active', 'success', 'info', 'warning', 'danger'];
	if (index%2 == 0){
		return{
			classes: classes[index%5]
		};
	}
	return {};
}

function changeDisByPermit(){
    if ($("#userName").attr("permit") == "0"){
        $("#dropdownMenu").attr("class","active dropdown");
        $("#moreMenu").attr("class","dropdown-toggle");
    }else{
        $("#dropdownMenu").attr("class","active dropdown disabled");
        $("#moreMenu").attr("class","dropdown-toggle disabled");
    }
}