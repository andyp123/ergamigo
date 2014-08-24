// use a string for now
var csv_data = "time,distance,spm,power,pace,calhr,calories,heartrate,status,forceplot\n" + 
  "1.3,2.0,0,0,0,0,0,0,9,3,3,12,12,12,12,14,14,14,15,15,15,14,14,14,14,12,12,12,8,8,8,8,5,5,5,2,2,2,1,1,1,1\n" + 
  "2.82,4.2,50,10,327.106631019,334.416,0,0,9,8,12,12,12,12,14,14,14,13,13,13,13,12,12,12,9,9,9,9,7,7,7,5,5,5,3,3,3,3,2,2,2\n" + 
  "7.24,10.1,41,9,338.798785605,330.9744,0,0,9,3,10,10,10,10,20,20,20,29,29,29,29,35,35,35,35,39,39,39,40,40,40,40,40,40,40,40,40,40,39,39,39,37,37,37,32,32,32,21,21,21,11,11,11,11,3,3,3,0,0,0\n" + 
  "8.9,12.8,13,7,368.403149864,324.0912,0,0,9,11,17,17,17,24,24,24,26,26,26,27,27,27,27,27,27,28,28,28,30,30,30,29,29,26,26,26,24,24,24,20,20,20,14,14,14,7,7,2,2,2,0,0,0\n" + 
  "10.85,16.2,38,13,299.714828725,344.7408,0,0,9,14,14,26,26,26,38,38,38,47,47,55,55,55,62,62,66,66,66,70,70,72,72,72,73,73,75,75,78,78,78,78,77,77,76,76,75,75,74,74,76,76,76,76,72,72,69,69,65,65,63,63,60,56,56,52,52,45,45,36,28,28,20,20,15,15,2,0,0\n" + 
  "14.06,24.4,26,24,244.31620148,382.5984,1,0,9,24,24,31,31,38,38,44,44,50,50,57,57,65,65,72,72,78,78,81,81,82,82,80,80,80,78,78,77,77,76,73,73,69,69,72,72,71,71,71,68,64,64,57,57,50,39,39,30,18,18,6,6,0\n" + 
  "20.75,40.6,20,53,187.613488248,482.4048,1,0,1,\n"; 


function run() {
	var json_data = parse(csv_data);
	console.log(json_data);

	var output_str = "";
	var keys = json_data.keys;
	var strokes = json_data.strokes;

	for (var i = 0; i < strokes.length; ++i) {
		var stroke_str = "STROKE " + i + "\n----------\n";
		var stroke = strokes[i];
		for (var j = 0; j < keys.length; ++j) {
			var key = keys[j];
			var value = stroke[key];
			stroke_str += "\"" + key + "\" : " + value + "\n";
		}
		output_str += stroke_str + "\n";
	}

	document.getElementById("output").innerHTML = output_str; //JSON.stringify(json_data, null, 2);
}

function parse(str_data) {
	str_data = str_data.trim();
	var lines = str_data.split("\n") || [];
	var keys = lines[0].split(",") || [];
	var data = {};
	var strokes = [];

	for (var i = 1; i < lines.length; ++i) {
		var stroke_data = lines[i].split(",") || [];
		var stroke = {};
		for (var j = 0; j < keys.length; ++j) {
			if (keys[j] == "forceplot") {
				var force_data = [];
				for (var k = j; k < stroke_data.length; ++k) {
					force_data[k - j] = parseFloat(stroke_data[k]) || 0.0;
				}
				stroke[keys[j]] = force_data;
			} else {
				stroke[keys[j]] = parseFloat(stroke_data[j]);
			}
		}
		strokes[i - 1] = stroke;
	}

	data.keys = keys;
	data.strokes = strokes;
	return data;
}