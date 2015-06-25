# This module is written in CoffeeScript, a little language built on
# Javascript with Python-ish syntax. For a real project, this file would
# be automatically translated to pure Javascript and put in a
# static-files directory for serving.
#
# This module is used in the context of a module loader called
# Require.js that asynchronously loads static assets (such as other
# javascripts), useful for large sites with many modular components that
# are not all needed at once. This is what the "define" call does.
#
# Rather than have the server fetch all of any number of "tasks"
# associated with a given "material" at once, this module will fetch
# individual resources on demand as users select them.

define [
  "base",
  "JsmolViewer",
  "text!#{PATH}detail/structures_table.html",
  "highcharts"],
(base, JsmolViewer, structTmpl) ->
  class TasksDetail
    constructor: (taskIds) ->
      $("#tasks-nav").listRadio().find("a").click (e) =>
        @loadDetails $(e.currentTarget).attr("href").replace("#", "")
      if window.location.hash
        $("a[href='#{window.location.hash}']").trigger('click')
      else
        @loadDetails taskIds.split(" ")[0]

    loadDetails: (id) ->
      $("#tasks-nav").after("<div id='loading' class='pull-down rotating fontastic-molecule'></div>")
      $(".detail").html('')
      jqxhr = $.get "/tasks/#{id}/json", (data) =>
        [calc1, calc2] = data.calculations
        data.incar = _.omit calc1.input.incar, "SYSTEM"
        data.kpoints = calc1.input.kpoints
        [kp] = data.kpoints.kpoints
        data.kpointsDivisions = if _.isArray(kp) then kp.join(", ") else kp
        if data.kpointsDivisions is "1, 1, 1" and data.kpoints.actual_points.length > 1
          data.kpointsDivisions = data.kpoints.actual_points.length
        for key, val of data.analysis
          data.analysis[key] = if _.isNumber val then val.toFixed(3) else val
        @render(data)
        if calc1.output.ionic_steps? and calc1?
          @chart1 = @createRelaxtionChart
            el: "chart1"
            series: @formatIonicSeries calc1.output.ionic_steps
            title: "Iterative steps in the first relaxation"
        if calc2?
          if calc2.output.ionic_steps?
            @chart2 = @createRelaxtionChart
              el: "chart2"
              series: @formatIonicSeries calc2.output.ionic_steps
              title: "Iterative steps in the second relaxation"
      jqxhr.fail -> $('.detail').html('Could not fetch task details. Please try again by clicking on one of the options above.')
      jqxhr.always -> $("#loading").remove()

    render: (data) ->
      # Although there are > 10 task types, there are only two templates
      if /optimize-structure/.test(_.slugify(data.task_type))
        @$taskTemplate = $("#ggau-optimize-structure-2x")
      else
        @$taskTemplate = $("#ggau-uniform")
      @template = _.template @$taskTemplate.html(), data
      $(".detail").html(@template)
      @createViewer data
      $("#final-structures").prepend _.template structTmpl,
        sites: _.groupSites data.output.crystal.sites
        lattice: data.output.crystal.lattice
        title: "Final Structure"
      $("#initial-structures").prepend _.template structTmpl,
        sites: _.groupSites data.input.crystal.sites
        lattice: data.input.crystal.lattice
        title: "Initial Structures"
      $(".download-cif").remove()

    createViewer: ({cif, cif_initial}) ->
      @viewer = new JsmolViewer {cif, selector: "#jsmol"}
      $("#input").change => @viewer.loadStructure cif_initial
      $("#output").change => @viewer.loadStructure cif

    getData : ({electronic_steps}, index) ->
      data = _.map electronic_steps, (es, i) ->
        x: i
        y: es.e_wo_entrp
        name: "Ionic Step #{index}, Electronic Step #{i}"
      if index is 0 then _.rest data else data

    formatIonicSeries: (steps) ->
      series = _.map steps, (step, i) =>
        name: "Ionic Step #{i}"
        data: @getData step, i
      numseries = series.length
      numtoadd = i = 0
      while i < numseries
        numdatapoints = series[i].data.length
        j = 0
        while j < numdatapoints
          series[i].data[j].x += numtoadd
          j++
        numtoadd += numdatapoints
        i++
      series

    createRelaxtionChart: ({el, series, title}) ->
      new Highcharts.Chart
        chart:
          renderTo: el
          backgroundColor: "transparent"
          defaultSeriesType: "line"
          zoomType: "x, y"
          height: 300
        legend:
          enabled: false
          align: "center"
          verticalAlign: "bottom"
          layout: "horizontal"
        xAxis:
          title:
            text: "Step (color change indicates new ionic step)"
          allowDecimals: false
        yAxis:
          title:
            text: "Energy (eV)"
        series: series
        tooltip:
          formatter: -> "" + @point.name + "<br />Energy: " + @y
          borderColor: "#fe6a00"
        title:
          text: title
        subtitle:
          text: "Click and drag to zoom"
        plotOptions:
          series:
            pointWidth: 5
            shadow: false
            states:
              hover:
                color: "#fe6a00"
        credits:
          enabled: false
