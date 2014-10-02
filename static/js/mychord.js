//*******************************************************************
//  DRAW THE CHORD DIAGRAM
//*******************************************************************
function drawChords (matrix, mmap) {
	var w = window.innerWidth - 50, h = window.innerHeight - 100, r1 = h / 2, r0 = r1 - 140;

	var fill = d3.scale.ordinal()
		.range(["#0A141F", "#0F1F2E", "#14293D", "#1A334C", "#1F3D5C", "#24476B","#29527A","#2E5C8A","#336699","#4775A3","#5C85AD","#7094B8","#85A3C2","#99B2CC","#ADC2D6","#C2D1E0"]);

	var chord = d3.layout.chord()
		.padding(.02)
		.sortSubgroups(d3.descending)
		.sortChords(d3.descending);

	var arc = d3.svg.arc()
		.innerRadius(r0)
		.outerRadius(r0 + 20);

	var svg = d3.select("body").append("svg:svg")
		.attr("width", w)
		.attr("height", h)
	  .append("svg:g")
		.attr("id", "circle")
		.attr("transform", "translate(" + w / 2 + "," + h / 2 + ")");

		svg.append("circle")
			.attr("r", r0 + 20);

	var rdr = chordRdr(matrix, mmap);
		chord.matrix(matrix);

	var g = svg.selectAll("g.group")
		.data(chord.groups())
	  .enter().append("svg:g")
		.attr("class", "group")
		.on("mouseover", mouseover)
		.on("mouseout", function (d) { d3.select("#tooltip").style("visibility", "hidden") });

	g.append("svg:path")
		.style("stroke", "black")
		.style("fill", function(d) { return fill(d.index); })
		.attr("d", arc);

	g.append("svg:text")
		.each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
		.attr("dy", ".35em")
		.style("font-family", "helvetica, arial, sans-serif")
		.style("font-size", "20px")
		.attr("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })
		.attr("transform", function(d) {
		  return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
			  + "translate(" + (r0 + 26) + ")"
			  + (d.angle > Math.PI ? "rotate(180)" : "");
		})
		.text(function(d) { return rdr(d).gname; });

	var chordPaths = svg.selectAll("path.chord")
			.data(chord.chords())
		  .enter().append("svg:path")
			.attr("class", "chord")
			.style("stroke", function(d) { return d3.rgb(fill(d.target.index)).darker(); })
			.style("fill", function(d) { return fill(d.target.index); })
			.attr("d", d3.svg.chord().radius(r0))
			.on("mouseover", function (d) {
			  d3.select("#tooltip")
				.style("visibility", "visible")
				.html(chordTip(rdr(d)))
				.style("top", function () { return (d3.event.pageY - 100)+"px"})
				.style("left", function () { return (d3.event.pageX - 100)+"px";})
			})
			.on("mouseout", function (d) { d3.select("#tooltip").style("visibility", "hidden") });

	function chordTip (d) {
		var p = d3.format(".2%"), q = d3.format(",.3r")
		return "Chord Info:<br/>"
		  + d.sname + " co-occurs with " + d.tname
		  + " (MI: " + q(d.svalue) + ") "
		  + (d.sname === d.tname ? "": (""))
	}

	function groupTip (d) {
		var p = d3.format(".1%"), q = d3.format(",.3r")
		return "Group Info:<br/>"
			+ d.gname + "<br/>"
	}

	function mouseover(d, i) {
		d3.select("#tooltip")
		  .style("visibility", "visible")
		  .html(groupTip(rdr(d)))
		  .style("top", function () { return (d3.event.pageY - 80)+"px"})
		  .style("left", function () { return (d3.event.pageX - 130)+"px";})

		chordPaths.classed("fade", function(p) {
		  return p.source.index != i
			  && p.target.index != i;
		});
	}
}