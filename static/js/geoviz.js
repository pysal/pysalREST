// Author: xunli at asu.edu

var GPoint = function( x, y ) {
  this.x = x;
  this.y = y;
};

GPoint.prototype = {
};

var GRect = function( x0, y0, x1, y1 ) {
  this.x0 = x0;
  this.y0 = y0;
  this.x1 = x1;
  this.y1 = y1;
};

GRect.prototype = {
  Contains: function( gpoint ) {
    return gpoint.x >= this.x0 && gpoint.x <= this.x1 && gpoint.y >= this.y0
           && gpoint.y <= this.y1;
  },
  GetW: function() {
    return this.x1 - this.x0;
  },
  GetH: function() {
    return this.y1 - this.y0;
  },
};

var GeoVizMap = function(geojson, mapcanvas, extent) {
  this.HLT_BRD_CLR = "black";
  this.HLT_CLR = "yellow";
  this.STROKE_CLR = "#CCCCCC";
  this.FILL_CLR = "green";
  this.LINE_WIDTH = 1;
  
  // members
  this.geojson = geojson;
  this.mapcanvas = mapcanvas;
  this.width = window.innerWidth;//mapcanvas.width;
  this.height = window.innerHeight; //mapcanvas.height;
  this.mapcanvas.width = this.width;
  this.mapcanvas.height = this.height;

  this.bbox = [];
  this.centroids = [];
  this.extent = extent;
  if ( extent == undefined ) this.extent = this.getExtent();
  this.mapWidth = this.extent[1] - this.extent[0];
  this.mapHeight = this.extent[3] - this.extent[2];

  this.updateTransf();
  
  _self = this;
  
  this.selected = [];
  this.brushRect = undefined;
  this.isBrushing = false;
  this.startX = -1;
  this.startY = -1;
  this.startPX = undefined;
  this.startPY = undefined;
  this.isMouseDown = false;
  this.isMouseUp = false;
  this.isMouseMove = false;
  this.isKeyDown = false;
  
  this.mapcanvas.addEventListener('mousemove', this.OnMouseMove, false);
  this.mapcanvas.addEventListener('mousedown', this.OnMouseDown, false);
  this.mapcanvas.addEventListener('mouseup', this.OnMouseUp, false);
  //this.mapcanvas.addEventListener('keydown', this.OnKeyDown, true);
  window.addEventListener('keypress', this.OnKeyDown, true);
  window.addEventListener('resize', this.OnResize, true);
  
  this.draw();
  this.buffer = this.createBuffer(this.mapcanvas);
  
};

// multi constructors
//GeoVizMap.fromComponents = function(geojson_url, canvas) {};
//GeoVizMap.fromComponents = function(zipfile_url, canvas) {};

// static functions
//GeoVizMap.version = function() {
//  return GeoVizMap.version;
//};

//
GeoVizMap.prototype = {
  // static vars
  version: "0.1",

  // member functions
  updateTransf: function() {
    var whRatio = this.mapWidth / this.mapHeight,
        xyRatio = this.width / this.height;
    this.offsetX = 0.0;
    this.offsetY = 0.0; 
    if ( xyRatio > whRatio ) {
      this.offsetX = (this.width - this.height * whRatio) / 2.0;
    } else if ( xyRatio < whRatio ) {
      this.offsetY = (this.height - this.width / whRatio) / 2.0;
    }
    this.scaleX = d3.scale.linear()
                    .domain([this.extent[0], this.extent[1]])
                    .range([0, this.width - this.offsetX * 2]);
    this.scaleY = d3.scale.linear()
                  .domain([this.extent[2], this.extent[3]])
                  .range([this.height - this.offsetY * 2, 0]);
    this.scalePX = d3.scale.linear()
                    .domain([0, this.width - this.offsetX * 2])
                    .range([this.extent[0], this.extent[1]]);
    this.scalePY = d3.scale.linear()
                  .domain([this.height - this.offsetY * 2, 0])
                  .range([this.extent[2], this.extent[3]]);
  },
  mapToScreen: function(px,py) {
    var x = this.scaleX(px) + this.offsetX;
    var y = this.scaleY(py) + this.offsetY;
    return [x, y];
  },
  screenToMap: function(x,y) {
    var px = this.scalePX(x - this.offsetX);
    var py = this.scalePY(y - this.offsetY);
    return [px, py];
  },
  getExtent: function() {
    var minX = Number.POSITIVE_INFINITY,
        maxX = Number.NEGATIVE_INFINITY,
        minY = Number.POSITIVE_INFINITY,
        maxY = Number.NEGATIVE_INFINITY;
    this.bbox = [];
    that = this;
    this.geojson.features.forEach(function(feat,i) {
      var bminX = Number.POSITIVE_INFINITY,
          bmaxX = Number.NEGATIVE_INFINITY,
          bminY = Number.POSITIVE_INFINITY,
          bmaxY = Number.NEGATIVE_INFINITY;
      feat.geometry.coordinates.forEach(function(coords,j) {
        coords.forEach( function( xy,k ) {
          x = xy[0], y = xy[1];
          if (x > maxX) {maxX = x;}
          if (x < minX) {minX = x;}
          if (y > maxY) {maxY = y;}
          if (y < minY) {minY = y;}
          if (x > bmaxX) {bmaxX = x;}
          if (x < bminX) {bminX = x;}
          if (y > bmaxY) {bmaxY = y;}
          if (y < bminY) {bminY = y;}
        });
      });
      that.bbox.push([bminX, bmaxX, bminY, bmaxY]);
      that.centroids.push([bminX + ((bmaxX - bminX)/2.0), bminY + ((bmaxY - bminY)/2.0)]);
    });
    console.log(minX, maxX, minY, maxY)
    return [minX, maxX, minY, maxY];
  },

  // create buffer canvas
  createBuffer: function() {
    var _buffer = document.createElement("canvas");
    _buffer.width = this.mapcanvas.width;
    _buffer.height = this.mapcanvas.height;
    var bufferCtx = _buffer.getContext("2d");
    bufferCtx.drawImage(this.mapcanvas, 0, 0);
    return _buffer;
  },

  highlight: function( ids ) {
    var context = _self.mapcanvas.getContext("2d");
    context.clearRect(0, 0, _self.width, _self.height);
    context.drawImage( _self.buffer, 0, 0);
    context.lineWidth = 1;
    context.strokeStyle = "#00ffff";
    context.fillStyle = "yellow";
    ids.forEach( function( id) {
      _self.geojson.features[id].geometry.coordinates.forEach(
        function( coords, j ) {
          context.beginPath();
          coords.forEach( function(xy,k) {
            var x = xy[0], y = xy[1];
            x = _self.scaleX(x)+ _self.offsetX;
            y = _self.scaleY(y)+ _self.offsetY;
  
            if (k === 0) {
              context.moveTo(x,y);
            } else {
              context.lineTo(x,y);
            }
          });
          context.closePath();
          context.stroke();
          context.fill();
        }
      );
    });
    localStorage["highlight"] = ids.toString();
    if (window.opener) {
      console.log(window.opener.highlighted);
    }
  },
  
  drawPolygon: function( ctx, plg, stk_clr, fill_clr) {
    plg.geometry.coordinates.forEach( function( coords, j ) {
      ctx.beginPath();
      coords.forEach( function( xy, k ) {
        var x = xy[0], y = xy[1];
        x = _self.scaleX(x)+ _self.offsetX;
        y = _self.scaleY(y)+ _self.offsetY;
        if (k === 0) {
          ctx.moveTo(x,y);
        } else {
          ctx.lineTo(x,y);
        }
      });
      ctx.closePath();
      if ( stk_clr ) ctx.strokeStyle = stk_clr;
      ctx.stroke();
      if ( fill_clr ) ctx.fillStyle = fill_clr;
      ctx.fill();
    });
  },
  
  draw: function() {
    //console.log(this.geojson);
    var context = this.mapcanvas.getContext("2d");
    context.imageSmoothingEnabled= false;
    context.lineWidth = _self.LINE_WIDTH;

    var that = this;
    this.geojson.features.forEach( function(feat,i) {
      that.drawPolygon( context, feat, that.STROKE_CLR, that.FILL_CLR );
    });

  }, 
  
  // register mouse events of canvas
  OnResize: function( e) {
    _self.width = window.innerWidth * 0.8;//mapcanvas.width;
    _self.height = window.innerHeight * 0.8; //mapcanvas.height;
    _self.mapcanvas.width = _self.width;
    _self.mapcanvas.height = _self.height;
    _self.updateTransf();
    _self.draw();
    _self.buffer = _self.createBuffer(_self.mapcanvas);
  },
  OnKeyDown: function( e ) {
    console.log(e.keyCode);
    if ( e.keyCode == 115 ) {
      _self.isKeyDown = true;
    }
  },
  OnMouseDown: function( evt ) {
    var x = evt.pageX, y = evt.pageY;
    _self.isMouseDown = true;
    _self.startX = x;
    _self.startY = y;
    console.log("isKeyDown:", _self.isKeyDown);
    if ( _self.isKeyDown == true ) {
      if (_self.brushRect && _self.brushRect.Contains(new GPoint(x, y)) ) {
        console.log("brushing");
        _self.isBrushing = true;
      }
    }
    if (_self.brushRect && !_self.brushRect.Contains(new GPoint(x, y)) ) {
      console.log("cancel brushing");
      var context = _self.mapcanvas.getContext("2d");
      context.clearRect(0, 0, _self.width, _self.height);
      context.drawImage( _self.buffer, 0, 0);
      _self.brushRect = undefined;
      _self.isBrushing = false;
    }
  },
  OnMouseMove: function(evt) {
    var x = evt.pageX, y = evt.pageY;
    var startX, startY;
    if ( _self.isMouseDown == true ) {
      var context = _self.mapcanvas.getContext("2d");
      context.imageSmoothingEnabled= false;
      context.clearRect(0, 0, _self.width, _self.height);
      context.drawImage( _self.buffer, 0, 0);
      // draw a selection box
      context.beginPath();
      if ( _self.isBrushing == true ) {
        var offsetX = x - _self.startX,
            offsetY = y - _self.startY;
        startX = _self.brushRect.x0 + offsetX;
        startY = _self.brushRect.y0 + offsetY;
        context.rect( startX, startY, _self.brushRect.GetW(), _self.brushRect.GetH() );
      } else {
        startX = _self.startX;
        startY = _self.startY;
        var w = x - startX, h = y - startY;
        context.rect( startX, startY, w, h);
      }
      context.strokeStyle = _self.HLT_BRD_CLR;
      context.stroke();
      
      // highlight selection
      var pt0 = _self.screenToMap(startX, startY), pt1;
      if ( _self.isBrushing == true ) {
        pt1 = _self.screenToMap(startX + _self.brushRect.GetW(), startY + _self.brushRect.GetH());
      } else {
        pt1 = _self.screenToMap(x,y);
      } 
      if ( x == _self.startX && y == _self.startY ) {
        _self.bbox.forEach( function( box, i ) {
          if ( pt1[0] >= box[0] && pt1[0] <= box[1] 
               && pt1[1] >= box[2] && pt1[1] <= box[3] ) {
            _self.highlight([i]);
            _self.isMouseDown = false;
            return;
          }
        });
      } else {
        var minPX = Math.min( pt0[0], pt1[0]),
            maxPX = Math.max( pt0[0], pt1[0]),
            minPY = Math.min( pt0[1], pt1[1]),
            maxPY = Math.max( pt0[1], pt1[1]);
        context.lineWidth = 1;
        _self.selected = [];
        _self.centroids.forEach( function( pt, i ) {
          if ( pt[0] >= minPX && pt[0] <= maxPX 
              && pt[1] >= minPY && pt[1] <= maxPY) {
            _self.drawPolygon( context, _self.geojson.features[i], undefined, _self.HLT_CLR );
            _self.selected.push(i);
          }
        });
        localStorage["highlight"] = _self.selected.toString();
      }
    }
  },
  OnMouseUp: function(evt) {
    var x = evt.pageX, y = evt.pageY;
    if ( _self.isMouseDown == true) {
      if ( _self.isKeyDown == true ) {
        _self.brushRect = new GRect( _self.startX, _self.startY, x, y);
      }
    }
    _self.isMouseDown = false;
  },
  
};