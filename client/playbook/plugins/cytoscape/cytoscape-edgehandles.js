/*!
Copyright (c) The Cytoscape Consortium

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

;( function($$) {
  'use strict';

  var whitespace = /\s+/;

  var $ = function(d){
    var dataKey = '_cytoscapeEdgehandlesData';
    var listenerKey = '_cytoscapeEdgehandlesListeners';

    return {
      0: d,
      addClass: function( cls ){
        this.toggleClass( cls, true );
      },
      removeClass: function( cls ){
        this.toggleClass( cls, true );
      },
      toggleClass: function( cls, bool ){
        this[0].classList.toggle( cls, bool );
      },
      data: function( name, val ){
        var k = dataKey;
        var data = this[0][k] = this[0][k] || {};

        if ( val === undefined ) {
          return data[ name ];
        } else {
          data[ name ] = val;
        }

        return this;
      },
      trigger: function(eventName){
        var evt = new Event(eventName);

        this[0].dispatchEvent(evt);

        return this;
      },
      append: function(ele) {
        this[0].appendChild( ele[0] || ele );

        return this;
      },
      attr: function( name, val ) {
        if (val === undefined) {
          return this[0].getAttribute( name );
        } else {
          this[0].setAttribute( name, val );
        }

        return this;
      },
      offset: function() {
        var rect = this[0].getBoundingClientRect();

        return {
          top: rect.top + window.pageYOffset,
          left: rect.left + window.pageXOffset
        };
      },
      listeners: function( name ){
        var k = listenerKey;
        var l = this[0][k] = this[0][k] || {};

        l[ name ] = l[ name ] || [];

        return l[ name ];
      },
      on: function(name, listener, one) {
        name.split( whitespace ).forEach(function(n){
          var wrappedListener = (function( e ){
            e.originalEvent = e;

            if( one ){
              this.off( n, wrappedListener );
            }

            listener.apply( this[0], [ e ] );
          }).bind( this );

          this.listeners(n).push({
            wrapped: wrappedListener,
            passed: listener
          });

          this[0].addEventListener( n, wrappedListener );
        }, this);

        return this;
      },
      bind: function(name, listener){
        return this.on( name, listener );
      },
      off: function(name, listener){
        name.split( whitespace ).forEach(function(n) {
          var liss = this.listeners(n);

          for( var i = liss.length - 1; i >= 0; i-- ){
            var lis = liss[i];

            if( lis.wrapped === listener || lis.passed === listener ){
              this[0].removeEventListener( n, lis.wrapped );

              liss.splice( i, 1 );
            }
          }
        }, this);

        return this;
      },
      one: function(name, listener) {
        return this.on( name, listener, true );
      },
      height: function(){
        return this[0].clientHeight;
      },
      width: function(){
        return this[0].clientWidth;
      }
    };
  };

  var debounce = (function(){
    /**
     * lodash 3.1.1 (Custom Build) <https://lodash.com/>
     * Build: `lodash modern modularize exports="npm" -o ./`
     * Copyright 2012-2015 The Dojo Foundation <http://dojofoundation.org/>
     * Based on Underscore.js 1.8.3 <http://underscorejs.org/LICENSE>
     * Copyright 2009-2015 Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
     * Available under MIT license <https://lodash.com/license>
     */
    /** Used as the `TypeError` message for "Functions" methods. */
    var FUNC_ERROR_TEXT = 'Expected a function';

    /* Native method references for those with the same name as other `lodash` methods. */
    var nativeMax = Math.max,
        nativeNow = Date.now;

    /**
     * Gets the number of milliseconds that have elapsed since the Unix epoch
     * (1 January 1970 00:00:00 UTC).
     *
     * @static
     * @memberOf _
     * @category Date
     * @example
     *
     * _.defer(function(stamp) {
     *   console.log(_.now() - stamp);
     * }, _.now());
     * // => logs the number of milliseconds it took for the deferred function to be invoked
     */
    var now = nativeNow || function() {
      return new Date().getTime();
    };

    /**
     * Creates a debounced function that delays invoking `func` until after `wait`
     * milliseconds have elapsed since the last time the debounced function was
     * invoked. The debounced function comes with a `cancel` method to cancel
     * delayed invocations. Provide an options object to indicate that `func`
     * should be invoked on the leading and/or trailing edge of the `wait` timeout.
     * Subsequent calls to the debounced function return the result of the last
     * `func` invocation.
     *
     * **Note:** If `leading` and `trailing` options are `true`, `func` is invoked
     * on the trailing edge of the timeout only if the the debounced function is
     * invoked more than once during the `wait` timeout.
     *
     * See [David Corbacho's article](http://drupalmotion.com/article/debounce-and-throttle-visual-explanation)
     * for details over the differences between `_.debounce` and `_.throttle`.
     *
     * @static
     * @memberOf _
     * @category Function
     * @param {Function} func The function to debounce.
     * @param {number} [wait=0] The number of milliseconds to delay.
     * @param {Object} [options] The options object.
     * @param {boolean} [options.leading=false] Specify invoking on the leading
     *  edge of the timeout.
     * @param {number} [options.maxWait] The maximum time `func` is allowed to be
     *  delayed before it's invoked.
     * @param {boolean} [options.trailing=true] Specify invoking on the trailing
     *  edge of the timeout.
     * @returns {Function} Returns the new debounced function.
     * @example
     *
     * // avoid costly calculations while the window size is in flux
     * jQuery(window).on('resize', _.debounce(calculateLayout, 150));
     *
     * // invoke `sendMail` when the click event is fired, debouncing subsequent calls
     * jQuery('#postbox').on('click', _.debounce(sendMail, 300, {
     *   'leading': true,
     *   'trailing': false
     * }));
     *
     * // ensure `batchLog` is invoked once after 1 second of debounced calls
     * var source = new EventSource('/stream');
     * jQuery(source).on('message', _.debounce(batchLog, 250, {
     *   'maxWait': 1000
     * }));
     *
     * // cancel a debounced call
     * var todoChanges = _.debounce(batchLog, 1000);
     * Object.observe(models.todo, todoChanges);
     *
     * Object.observe(models, function(changes) {
     *   if (_.find(changes, { 'user': 'todo', 'type': 'delete'})) {
     *     todoChanges.cancel();
     *   }
     * }, ['delete']);
     *
     * // ...at some point `models.todo` is changed
     * models.todo.completed = true;
     *
     * // ...before 1 second has passed `models.todo` is deleted
     * // which cancels the debounced `todoChanges` call
     * delete models.todo;
     */
    function debounce(func, wait, options) {
      var args,
          maxTimeoutId,
          result,
          stamp,
          thisArg,
          timeoutId,
          trailingCall,
          lastCalled = 0,
          maxWait = false,
          trailing = true;

      if (typeof func != 'function') {
        throw new TypeError(FUNC_ERROR_TEXT);
      }
      wait = wait < 0 ? 0 : (+wait || 0);
      if (options === true) {
        var leading = true;
        trailing = false;
      } else if (isObject(options)) {
        leading = !!options.leading;
        maxWait = 'maxWait' in options && nativeMax(+options.maxWait || 0, wait);
        trailing = 'trailing' in options ? !!options.trailing : trailing;
      }

      function cancel() {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        if (maxTimeoutId) {
          clearTimeout(maxTimeoutId);
        }
        lastCalled = 0;
        maxTimeoutId = timeoutId = trailingCall = undefined;
      }

      function complete(isCalled, id) {
        if (id) {
          clearTimeout(id);
        }
        maxTimeoutId = timeoutId = trailingCall = undefined;
        if (isCalled) {
          lastCalled = now();
          result = func.apply(thisArg, args);
          if (!timeoutId && !maxTimeoutId) {
            args = thisArg = undefined;
          }
        }
      }

      function delayed() {
        var remaining = wait - (now() - stamp);
        if (remaining <= 0 || remaining > wait) {
          complete(trailingCall, maxTimeoutId);
        } else {
          timeoutId = setTimeout(delayed, remaining);
        }
      }

      function maxDelayed() {
        complete(trailing, timeoutId);
      }

      function debounced() {
        args = arguments;
        stamp = now();
        thisArg = this;
        trailingCall = trailing && (timeoutId || !leading);

        if (maxWait === false) {
          var leadingCall = leading && !timeoutId;
        } else {
          if (!maxTimeoutId && !leading) {
            lastCalled = stamp;
          }
          var remaining = maxWait - (stamp - lastCalled),
              isCalled = remaining <= 0 || remaining > maxWait;

          if (isCalled) {
            if (maxTimeoutId) {
              maxTimeoutId = clearTimeout(maxTimeoutId);
            }
            lastCalled = stamp;
            result = func.apply(thisArg, args);
          }
          else if (!maxTimeoutId) {
            maxTimeoutId = setTimeout(maxDelayed, remaining);
          }
        }
        if (isCalled && timeoutId) {
          timeoutId = clearTimeout(timeoutId);
        }
        else if (!timeoutId && wait !== maxWait) {
          timeoutId = setTimeout(delayed, wait);
        }
        if (leadingCall) {
          isCalled = true;
          result = func.apply(thisArg, args);
        }
        if (isCalled && !timeoutId && !maxTimeoutId) {
          args = thisArg = undefined;
        }
        return result;
      }
      debounced.cancel = cancel;
      return debounced;
    }

    /**
     * Checks if `value` is the [language type](https://es5.github.io/#x8) of `Object`.
     * (e.g. arrays, functions, objects, regexes, `new Number(0)`, and `new String('')`)
     *
     * @static
     * @memberOf _
     * @category Lang
     * @param {*} value The value to check.
     * @returns {boolean} Returns `true` if `value` is an object, else `false`.
     * @example
     *
     * _.isObject({});
     * // => true
     *
     * _.isObject([1, 2, 3]);
     * // => true
     *
     * _.isObject(1);
     * // => false
     */
    function isObject(value) {
      // Avoid a V8 JIT bug in Chrome 19-20.
      // See https://code.google.com/p/v8/issues/detail?id=2291 for more details.
      var type = typeof value;
      return !!value && (type == 'object' || type == 'function');
    }

    return debounce;

  })();

  // ported lodash throttle function
  var throttle = function( func, wait, options ){
    var leading = true,
        trailing = true;

    if( options === false ){
      leading = false;
    } else if( typeof options === typeof {} ){
      leading = 'leading' in options ? options.leading : leading;
      trailing = 'trailing' in options ? options.trailing : trailing;
    }
    options = options || {};
    options.leading = leading;
    options.maxWait = wait;
    options.trailing = trailing;

    return debounce( func, wait, options );
  };

  // registers the extension on a cytoscape lib ref
  var register = function( $$ ) {
    if( !$$ ) {
      return;
    } // can't register if cytoscape unspecified

    var defaults = {
      preview: true, // whether to show added edges preview before releasing selection
      stackOrder: 4, // Controls stack order of edgehandles canvas element by setting it's z-index
      handleSize: 10, // the size of the edge handle put on nodes
      handleIcon: false,
      handleColor: '#ff0000', // the colour of the handle and the line drawn from it
      handleLineType: 'ghost', // can be 'ghost' for real edge, 'straight' for a straight line, or 'draw' for a draw-as-you-go line
      handleLineWidth: 1, // width of handle line in pixels
      handleOutlineColor: '#000000', // the colour of the handle outline
      handleOutlineWidth: 0, // the width of the handle outline in pixels
      handleNodes: 'node', // selector/filter function for whether edges can be made from a given node
      handlePosition: 'middle top', // sets the position of the handle in the format of "X-AXIS Y-AXIS" such as "left top", "middle top"
      hoverDelay: 150, // time spend over a target node before it is considered a target selection
      cxt: false, // whether cxt events trigger edgehandles (useful on touch)
      enabled: true, // whether to start the plugin in the enabled state
      toggleOffOnLeave: false, // whether an edge is cancelled by leaving a node (true), or whether you need to go over again to cancel (false; allows multiple edges in one pass)
      edgeType: function( sourceNode, targetNode ) {
        // can return 'flat' for flat edges between nodes or 'node' for intermediate node between them
        // returning null/undefined means an edge can't be added between the two nodes
        return 'flat';
      },
      loopAllowed: function( node ) {
        // for the specified node, return whether edges from itself to itself are allowed
        return false;
      },
      nodeLoopOffset: -50, // offset for edgeType: 'node' loops
      nodeParams: function( sourceNode, targetNode ) {
        // for edges between the specified source and target
        // return element object to be passed to cy.add() for intermediary node
        return {};
      },
      edgeParams: function( sourceNode, targetNode, i ) {
        // for edges between the specified source and target
        // return element object to be passed to cy.add() for edge
        // NB: i indicates edge index in case of edgeType: 'node'
        return {};
      },
      start: function( sourceNode ) {
        // fired when edgehandles interaction starts (drag on handle)
      },
      complete: function( sourceNode, targetNodes, addedEntities ) {
        // fired when edgehandles is done and entities are added
      },
      stop: function( sourceNode ) {
        // fired when edgehandles interaction is stopped (either complete with added edges or incomplete)
      }, 
      cancel: function( sourceNode, renderedPosition ) {
        // fired when edgehandles are cancelled ( incomplete - nothing has been added ) - renderedPosition is where the edgehandle was released
      }
    };

    var edgehandles = function( params ) {
      var cy = this;
      var fn = params;
      var container = cy.container();

      var functions = {
        destroy: function() {
          var $container = $( this );
          var data = $container.data( 'cyedgehandles' );

          if( data == null ) {
            return;
          }

          data.unbind();
          $container.data( 'cyedgehandles', {} );

          return $container;
        },

        option: function( name, value ) {
          var $container = $( this );
          var data = $container.data( 'cyedgehandles' );

          if( data == null ) {
            return;
          }

          var options = data.options;

          if( value === undefined ) {
            if( typeof name == typeof {} ) {
              var newOpts = name;
              options =Object.assign( {}, defaults, newOpts );
              data.options = options;
            } else {
              return options[ name ];
            }
          } else {
            options[ name ] = value;
          }

          $container.data( 'cyedgehandles', data );

          return $container;
        },

        disable: function() {
          return functions.option.apply( this, [ 'enabled', false ] );
        },

        enable: function() {
          return functions.option.apply( this, [ 'enabled', true ] );
        },

        resize: function() {
          var $container = $( this );

          $container.trigger( 'cyedgehandles.resize' );
        },

        drawon: function() {
          $( this ).trigger( 'cyedgehandles.drawon' );
        },

        drawoff: function() {
          $( this ).trigger( 'cyedgehandles.drawoff' );
        },

        init: function() {
          var self = this;
          var opts = Object.assign({}, defaults, params );
          var $container = $( this );
          var canvas = document.createElement('canvas');
          var $canvas = $(canvas);
          var handle;
          var line, linePoints;
          var mdownOnHandle = false;
          var grabbingNode = false;
          var inForceStart = false;
          var hx, hy, hr;
          var mx, my;
          var hoverTimeout;
          var drawsClear = true;
          var ghostNode;
          var ghostEdge;
          var sourceNode;
          var drawMode = false;
          cy.on( 'resize', function() {
            $container.trigger( 'cyedgehandles.resize' );
          });

          $container.append( $canvas );

          var _sizeCanvas = debounce( function(){
            $canvas
              .attr( 'height', $container.height() )
              .attr( 'width', $container.width() );
            canvas.setAttribute('style', 'position:absolute;top:0;left:0;z-index:'+opts.stackOrder);

            setTimeout(function(){
              var canvasBb = $canvas.offset();
              var containerBb = $container.offset();

              canvas
                .setAttribute('style', 'position:absolute;top:'+
                  (-( canvasBb.top - containerBb.top ))+
                  'px;left:'+(-( canvasBb.left - containerBb.left ))+
                  'px;z-index:'+opts.stackOrder);
            }, 0);
          }, 250 );

          var sizeCanvas = function(){
            clearDraws();
            _sizeCanvas();
          };

          sizeCanvas();

          var winResizeHandler;
          $( window ).bind( 'resize', winResizeHandler = function() {
            sizeCanvas();
          } );

          var ctrResizeHandler;
          $container.bind( 'cyedgehandles.resize', ctrResizeHandler = function() {
            sizeCanvas();
          } );

          var prevUngrabifyState;
          var ctrDrawonHandler;
          $container.on( 'cyedgehandles.drawon', ctrDrawonHandler = function() {
            drawMode = true;

            prevUngrabifyState = cy.autoungrabify();

            cy.autoungrabify( true );
          } );

          var ctrDrawoffHandler;
          $container.on( 'cyedgehandles.drawoff', ctrDrawoffHandler = function() {
            drawMode = false;

            cy.autoungrabify( prevUngrabifyState );
          } );

          var ctx = $canvas[ 0 ].getContext( '2d' );

          // write options to data
          var data = $container.data( 'cyedgehandles' );
          if( data == null ) {
            data = {};
          }
          data.options = opts;

          var optCache;

          function options() {
            return optCache || ( optCache = $container.data( 'cyedgehandles' ).options );
          }

          function enabled() {
            return options().enabled;
          }

          function disabled() {
            return !enabled();
          }

          function clearDraws() {

            if( drawsClear ) {
              return;
            } // break early to be efficient

            var w = $container.width();
            var h = $container.height();

            ctx.clearRect( 0, 0, w, h );
            drawsClear = true;
          }

          var lastPanningEnabled, lastZoomingEnabled, lastBoxSelectionEnabled;

          function disableGestures() {
            lastPanningEnabled = cy.panningEnabled();
            lastZoomingEnabled = cy.zoomingEnabled();
            lastBoxSelectionEnabled = cy.boxSelectionEnabled();

            cy
              .zoomingEnabled( false )
              .panningEnabled( false )
              .boxSelectionEnabled( false );
          }

          function resetGestures() {
            cy
              .zoomingEnabled( lastZoomingEnabled )
              .panningEnabled( lastPanningEnabled )
              .boxSelectionEnabled( lastBoxSelectionEnabled );
          }

          function resetToDefaultState() {

            clearDraws();

            //setTimeout(function(){
            cy.nodes()
              .removeClass( 'edgehandles-hover' )
              .removeClass( 'edgehandles-source' )
              .removeClass( 'edgehandles-target' );

            cy.$( '.edgehandles-ghost' ).remove();
            //}, 1);


            linePoints = null;

            sourceNode = null;

            resetGestures();
          }

          function makePreview( source, target ) {
            makeEdges( true );

            target.trigger( 'cyedgehandles.addpreview' );
          }

          function removePreview( source, target ) {
            source.edgesWith( target ).filter( '.edgehandles-preview' ).remove();

            target
              .neighborhood( 'node.edgehandles-preview' )
              .closedNeighborhood( '.edgehandles-preview' )
              .remove();

            target.trigger( 'cyedgehandles.removepreview' );

          }

          function drawHandle( hx, hy, hr ) {
            ctx.fillStyle = options().handleColor;
            ctx.strokeStyle = options().handleOutlineColor;

            ctx.beginPath();
            ctx.arc( hx, hy, hr, 0, 2 * Math.PI );
            ctx.closePath();
            ctx.fill();

            if(options().handleOutlineWidth) {
              ctx.lineWidth = options().handleLineWidth;
              ctx.stroke();
            }

            if(options().handleIcon){
               var icon = options().handleIcon;
               var width = icon.width*cy.zoom(), height = icon.height*cy.zoom();
               ctx.drawImage(icon, hx-(width/2), hy-(height/2), width, height);
            }

            drawsClear = false;
          }

          var lineDrawRate = 1000 / 60;

          var drawLine = throttle( function( hx, hy, x, y ) {

            // can't draw a line without having the starting node
            if( !sourceNode ){ return; }

            if( options().handleLineType !== 'ghost' ) {
              ctx.fillStyle = options().handleColor;
              ctx.strokeStyle = options().handleColor;
              ctx.lineWidth = options().handleLineWidth;
            }

            // draw line based on type
            switch( options().handleLineType ) {
              case 'ghost':

                if( !ghostNode || ghostNode.removed() ) {

                  drawHandle();

                  ghostNode = cy.add( {
                    group: 'nodes',
                    classes: 'edgehandles-ghost edgehandles-ghost-node',
                    css: {
                      'background-color': 'blue',
                      'width': 0.0001,
                      'height': 0.0001,
                      'opacity': 0,
                      'events': 'no'
                    },
                    position: {
                      x: 0,
                      y: 0
                    }
                  } );

                  ghostEdge = cy.add( {
                    group: 'edges',
                    classes: 'edgehandles-ghost edgehandles-ghost-edge',
                    data: {
                      source: sourceNode.id(),
                      target: ghostNode.id()
                    },
                    css: {
                      'events': 'no'
                    }
                  } );

                }

                ghostNode.renderedPosition( {
                  x: x,
                  y: y
                } );


                break;

              case 'straight':

                ctx.beginPath();
                ctx.moveTo( hx, hy );
                ctx.lineTo( x, y );
                ctx.closePath();
                ctx.stroke();

                break;
              case 'draw':
              default:

                if( linePoints == null ) {
                  linePoints = [ [ x, y ] ];
                } else {
                  linePoints.push( [ x, y ] );
                }

                ctx.beginPath();
                ctx.moveTo( hx, hy );

                for( var i = 0; i < linePoints.length; i++ ) {
                  var pt = linePoints[ i ];

                  ctx.lineTo( pt[ 0 ], pt[ 1 ] );
                }

                ctx.stroke();

                break;
            }

            if( options().handleLineType !== 'ghost' ) {
              drawsClear = false;
            }
          }, lineDrawRate, { leading: true } );

          function makeEdges( preview, src, tgt ) {

            // console.log('make edges', preview);

            var source = src ? src : cy.nodes( '.edgehandles-source' );
            var targets = tgt ? tgt : cy.nodes( '.edgehandles-target' );
            var classes = preview ? 'edgehandles-preview' : '';
            var added = cy.collection();

            if( !src && !tgt && !preview && options().preview ) {
              cy.$( '.edgehandles-ghost' ).remove();
            }

            if( source.size() === 0 || targets.size() === 0 ) {
              options().cancel(source, {x: mx, y: my});
              source.trigger( 'cyedgehandles.cancel', {x: mx, y: my});
              return; // nothing to do :(
            }

            // just remove preview class if we already have the edges
            if( !src && !tgt ) {
              if( !preview && options().preview ) {
                added = cy.elements( '.edgehandles-preview' ).removeClass( 'edgehandles-preview' );

                options().complete( source, targets, added );
                source.trigger( 'cyedgehandles.complete' );
                return;
              } else {
                // remove old previews
                cy.elements( '.edgehandles-preview' ).remove();
              }
            }

            for( var i = 0; i < targets.length; i++ ) {
              var target = targets[ i ];

              switch( options().edgeType( source, target ) ) {
                case 'node':

                  var p1 = source.position();
                  var p2 = target.position();
                  var p;

                  if( source.id() === target.id() ) {
                    p = {
                      x: p1.x + options().nodeLoopOffset,
                      y: p1.y + options().nodeLoopOffset
                    };
                  } else {
                    p = {
                      x: ( p1.x + p2.x ) / 2,
                      y: ( p1.y + p2.y ) / 2
                    };
                  }

                  var interNode = cy.add( Object.assign( {
                    group: 'nodes',
                    position: p
                  }, options().nodeParams( source, target ) ) ).addClass( classes );

                  var source2inter = cy.add( Object.assign( {
                    group: 'edges',
                    data: {
                      source: source.id(),
                      target: interNode.id()
                    }
                  }, options().edgeParams( source, target, 0 ) ) ).addClass( classes );

                  var inter2target = cy.add( Object.assign( {
                    group: 'edges',
                    data: {
                      source: interNode.id(),
                      target: target.id()
                    }
                  }, options().edgeParams( source, target, 1 ) ) ).addClass( classes );

                  added = added.add( interNode ).add( source2inter ).add( inter2target );

                  break;

                case 'flat':
                  var edge = cy.add( Object.assign( {
                    group: 'edges',
                    data: {
                      source: source.id(),
                      target: target.id()
                    }
                  }, options().edgeParams( source, target, 0 ) ) ).addClass( classes );

                  added = added.add( edge );

                  break;

                default:
                  target.removeClass( 'edgehandles-target' );
                  break; // don't add anything
              }
            }

            if( !preview ) {
              options().complete( source, targets, added );
              source.trigger( 'cyedgehandles.complete' );
            }
          }

          function hoverOver( node ) {
            var target = node;

            clearTimeout( hoverTimeout );
            hoverTimeout = setTimeout( function() {
              var source = cy.nodes( '.edgehandles-source' );

              var isLoop = node.hasClass( 'edgehandles-source' );
              var loopAllowed = options().loopAllowed( node );
              var isGhost = node.hasClass( 'edgehandles-ghost-node' );
              var noEdge = options().edgeType( source, node ) == null;

              if( isGhost || noEdge ) {
                return;
              }

              if( !isLoop || ( isLoop && loopAllowed ) ) {
                node.addClass( 'edgehandles-hover' );
                node.toggleClass( 'edgehandles-target' );

                if( options().preview ) {
                  if( node.hasClass( 'edgehandles-target' ) ) {
                    makePreview( source, target );
                  } else {
                    removePreview( source, target );
                  }
                }
              }
            }, options().hoverDelay );
          }

          function hoverOut( node ) {
            var target = node;

            node.removeClass( 'edgehandles-hover' );

            clearTimeout( hoverTimeout );

            if( options().toggleOffOnLeave ) {
              var source = sourceNode;

              node.removeClass( 'edgehandles-target' );
              removePreview( source, target );
            }
          }

          cy.ready( function( e ) {
            lastPanningEnabled = cy.panningEnabled();
            lastZoomingEnabled = cy.zoomingEnabled();
            lastBoxSelectionEnabled = cy.boxSelectionEnabled();

            // console.log('handles on ready')

            var lastActiveId;

            var transformHandler;
            cy.bind( 'zoom pan', transformHandler = function() {
              clearDraws();
            } );

            var lastMdownHandler;

            var startHandler, hoverHandler, leaveHandler, grabNodeHandler, freeNodeHandler, dragNodeHandler, forceStartHandler, removeHandler, cxtstartHandler, tapToStartHandler, cxtdragHandler, cxtdragoverHandler, cxtdragoutHandler, cxtendHandler, dragHandler, grabHandler;
            cy.on( 'mouseover tap', 'node', startHandler = function( e ) {
              var node = this;

              if( disabled() || drawMode || mdownOnHandle || grabbingNode || this.hasClass( 'edgehandles-preview' ) || inForceStart || this.hasClass( 'edgehandles-ghost-node' ) || node.filter( options().handleNodes ).length === 0 ) {
                return; // don't override existing handle that's being dragged
                // also don't trigger when grabbing a node etc
              }

              //console.log('mouseover startHandler %s %o', this.id(), this);

              if( lastMdownHandler ) {
                $container[ 0 ].removeEventListener( 'mousedown', lastMdownHandler, true );
                $container[ 0 ].removeEventListener( 'touchstart', lastMdownHandler, true );
              }

              var source = this;
              var p = node.renderedPosition();
              var h = node.renderedOuterHeight();
              var w = node.renderedOuterWidth();

              lastActiveId = node.id();

              // remove old handle
              clearDraws();

              hr = options().handleSize / 2 * cy.zoom();

              // store how much we should move the handle from origin(p.x, p.y)
              var moveX = 0;
              var moveY = 0;

              // grab axis's
              var axisX = options().handlePosition.split(' ')[0].toLowerCase();
              var axisY = options().handlePosition.split(' ')[1].toLowerCase();

              // based on handlePosition move left/right/top/bottom. Middle/middle will just be normal
              if(axisX == 'left') moveX = -(w / 2);
              else if(axisX == 'right') moveX = w / 2;
              if(axisY == 'top') moveY = -(h / 2);
              else if(axisY == 'bottom') moveY = h / 2;

              // set handle x and y based on adjusted positions
              hx = p.x + moveX;
              hy = p.y + moveY;

              // add new handle
              drawHandle( hx, hy, hr );

              node.trigger( 'cyedgehandles.showhandle' );


              function mdownHandler( e ) {
                $container[ 0 ].removeEventListener( 'mousedown', mdownHandler, true );
                $container[ 0 ].removeEventListener( 'touchstart', mdownHandler, true );

                var pageX = !e.touches ? e.pageX : e.touches[ 0 ].pageX;
                var pageY = !e.touches ? e.pageY : e.touches[ 0 ].pageY;
                var x = pageX - $container.offset().left;
                var y = pageY - $container.offset().top;
                var hrTarget = hr;

                if( e.button !== 0 && !e.touches ) {
                  return; // sorry, no right clicks allowed
                }

                if( Math.abs( x - hx ) > hrTarget || Math.abs( y - hy ) > hrTarget ) {
                  return; // only consider this a proper mousedown if on the handle
                }

                if( inForceStart ) {
                  return; // we don't want this going off if we have the forced start to consider
                }

                // console.log('mdownHandler %s %o', node.id(), node);

                mdownOnHandle = true;

                e.preventDefault();
                e.stopPropagation();

                sourceNode = node;

                node.addClass( 'edgehandles-source' );
                node.trigger( 'cyedgehandles.start' );

                function doneMoving( dmEvent ) {
                  // console.log('doneMoving %s %o', node.id(), node);

                  if( !mdownOnHandle || inForceStart ) {
                    return;
                  }

                  var $this = $( this );
                  mdownOnHandle = false;
                  $( window ).off( 'mousemove touchmove', moveHandler );

                  makeEdges();
                  resetToDefaultState();

                  options().stop( node );
                  node.trigger( 'cyedgehandles.stop' );
                }

                $( window ).one('mouseup touchend touchcancel blur', doneMoving )
                  .bind('mousemove touchmove', moveHandler );
                disableGestures();

                options().start( node );

                return false;
              }

              function moveHandler( e ) {
                // console.log('mousemove moveHandler %s %o', node.id(), node);

                var pageX = !e.touches ? e.pageX : e.touches[ 0 ].pageX;
                var pageY = !e.touches ? e.pageY : e.touches[ 0 ].pageY;
                var x = pageX - $container.offset().left;
                var y = pageY - $container.offset().top;

                mx = x; 
                my = y; 

                if( options().handleLineType !== 'ghost' ) {
                  clearDraws();
                  drawHandle( hx, hy, hr );
                }
                drawLine( hx, hy, x, y );


                return false;
              }

              $container[ 0 ].addEventListener( 'mousedown', mdownHandler, true );
              $container[ 0 ].addEventListener( 'touchstart', mdownHandler, true );
              lastMdownHandler = mdownHandler;


            } ).on( 'mouseover tapdragover', 'node', hoverHandler = function() {
              var node = this;
              var target = this;

              // console.log('mouseover hoverHandler')

              if( disabled() || drawMode || this.hasClass( 'edgehandles-preview' ) ) {
                return; // ignore preview nodes
              }

              if( mdownOnHandle ) { // only handle mdown case

                // console.log( 'mouseover hoverHandler %s $o', node.id(), node );

                hoverOver( node );

                return false;
              }

            } ).on( 'mouseout tapdragout', 'node', leaveHandler = function() {
              var node = this;

              if( drawMode ) {
                return;
              }

              if( mdownOnHandle ) {
                hoverOut( node );
              }

            } ).on( 'drag position', 'node', dragNodeHandler = function() {
              if( drawMode ) {
                return;
              }

              var node = this;

              if( !node.hasClass( 'edgehandles-ghost' ) ) {
                setTimeout( clearDraws, 50 );
              }

            } ).on( 'grab', 'node', grabHandler = function() {
              //grabbingNode = true;

              //setTimeout(function(){
              clearDraws();
              //}, 5);


            } ).on( 'drag', 'node', dragHandler = function() {
              grabbingNode = true;


            } ).on( 'free', 'node', freeNodeHandler = function() {
              grabbingNode = false;

            } ).on( 'cyedgehandles.forcestart', 'node', forceStartHandler = function() {
              var node = this;

              if( node.filter( options().handleNodes ).length === 0 ) {
                return; // skip if node not allowed
              }

              inForceStart = true;
              clearDraws(); // clear just in case

              var source = sourceNode = node;

              lastActiveId = node.id();

              node.trigger( 'cyedgehandles.start' );
              node.addClass( 'edgehandles-source' );

              var p = node.renderedPosition();
              var h = node.renderedOuterHeight();
              var w = node.renderedOuterWidth();

              var hr = options().handleSize / 2 * cy.zoom();
              var hx = p.x;
              var hy = p.y - h / 2;

              drawHandle( hx, hy, hr );

              node.trigger( 'cyedgehandles.showhandle' );

              // case: down and drag as normal
              var downHandler = function( e ) {

                $container[ 0 ].removeEventListener( 'mousedown', downHandler, true );
                $container[ 0 ].removeEventListener( 'touchstart', downHandler, true );

                var x = ( e.pageX !== undefined ? e.pageX : e.touches[ 0 ].pageX ) - $container.offset().left;
                var y = ( e.pageY !== undefined ? e.pageY : e.touches[ 0 ].pageY ) - $container.offset().top;
                var d = hr / 2;
                var onNode = p.x - w / 2 - d <= x && x <= p.x + w / 2 + d && p.y - h / 2 - d <= y && y <= p.y + h / 2 + d;

                if( onNode ) {
                  disableGestures();
                  mdownOnHandle = true; // enable the regular logic for handling going over target nodes

                  var moveHandler = function( me ) {
                    var x = ( me.pageX !== undefined ? me.pageX : me.touches[ 0 ].pageX ) - $container.offset().left;
                    var y = ( me.pageY !== undefined ? me.pageY : me.touches[ 0 ].pageY ) - $container.offset().top;

                    mx = x; 
                    my = y; 

                    if( options().handleLineType !== 'ghost' ) {
                      clearDraws();
                      drawHandle( hx, hy, hr );
                    }
                    drawLine( hx, hy, x, y );
                  }

                  $container[ 0 ].addEventListener( 'mousemove', moveHandler, true );
                  $container[ 0 ].addEventListener( 'touchmove', moveHandler, true );

                  $( window ).one( 'mouseup touchend blur', function() {
                    $container[ 0 ].removeEventListener( 'mousemove', moveHandler, true );
                    $container[ 0 ].removeEventListener( 'touchmove', moveHandler, true );

                    inForceStart = false; // now we're done so reset the flag
                    mdownOnHandle = false; // we're also no longer down on the node

                    makeEdges();

                    options().stop( node );
                    node.trigger( 'cyedgehandles.stop' );

                    cy.off( 'tap', 'node', tapHandler );
                    node.off( 'remove', removeBeforeHandler );
                    resetToDefaultState();
                  } );

                  e.stopPropagation();
                  e.preventDefault();
                  return false;
                }
              };

              $container[ 0 ].addEventListener( 'mousedown', downHandler, true );
              $container[ 0 ].addEventListener( 'touchstart', downHandler, true );

              var removeBeforeHandler;
              node.one( 'remove', function() {
                $container[ 0 ].removeEventListener( 'mousedown', downHandler, true );
                $container[ 0 ].removeEventListener( 'touchstart', downHandler, true );
                cy.off( 'tap', 'node', tapHandler );
              } );

              // case: tap a target node
              var tapHandler;
              cy.one( 'tap', 'node', tapHandler = function() {
                var target = this;

                var isLoop = source.id() === target.id();
                var loopAllowed = options().loopAllowed( target );

                if( !isLoop || ( isLoop && loopAllowed ) ) {
                  makeEdges( false, source, target );

                  //options().complete( node );
                  //node.trigger('cyedgehandles.complete');
                }

                inForceStart = false; // now we're done so reset the flag

                options().stop( node );
                node.trigger( 'cyedgehandles.stop' );

                $container[ 0 ].removeEventListener( 'mousedown', downHandler, true );
                $container[ 0 ].removeEventListener( 'touchstart', downHandler, true );
                node.off( 'remove', removeBeforeHandler );
                resetToDefaultState();
              } );


            } ).on( 'remove', 'node', removeHandler = function() {
              var id = this.id();

              if( id === lastActiveId ) {
                setTimeout( function() {
                  resetToDefaultState();
                }, 5 );
              }


            } ).on( 'cxttapstart tapstart', 'node', cxtstartHandler = function( e ) {
              var node = this;

              if( node.filter( options().handleNodes ).length === 0 ) {
                return; // skip if node not allowed
              }

              var cxtOk = options().cxt && e.type === 'cxttapstart';
              var tapOk = drawMode && e.type === 'tapstart';

              if( cxtOk || tapOk ) {

                clearDraws(); // clear just in case

                var node = sourceNode = this;
                var source = node;

                lastActiveId = node.id();

                node.trigger( 'cyedgehandles.start' );
                node.addClass( 'edgehandles-source' );

                var p = node.renderedPosition();
                var h = node.renderedOuterHeight();
                var w = node.renderedOuterWidth();

                hr = options().handleSize / 2 * cy.zoom();
                hx = p.x;
                hy = p.y - h / 2 - hr / 2;

                drawHandle( hx, hy, hr );

                node.trigger( 'cyedgehandles.showhandle' );

                options().start( node );
                node.trigger( 'cyedgehandles.start' );
              }


            } ).on( 'cxtdrag tapdrag', cxtdragHandler = function( e ) {
              var cxtOk = options().cxt && e.type === 'cxtdrag';
              var tapOk = drawMode && e.type === 'tapdrag';

              if( ( cxtOk || tapOk ) && sourceNode ) {
                var rpos = e.cyRenderedPosition;

                drawLine( hx, hy, rpos.x, rpos.y );

              }


            } ).on( 'cxtdragover tapdragover', 'node', cxtdragoverHandler = function( e ) {
              var cxtOk = options().cxt && e.type === 'cxtdragover';
              var tapOk = drawMode && e.type === 'tapdragover';

              if( ( cxtOk || tapOk ) && sourceNode ) {
                var node = this;

                hoverOver( node );
              }


            } ).on( 'cxtdragout tapdragout', 'node', cxtdragoutHandler = function( e ) {
              var cxtOk = options().cxt && e.type === 'cxtdragout';
              var tapOk = drawMode && e.type === 'tapdragout';

              if( ( cxtOk || tapOk ) && sourceNode ) {
                var node = this;

                hoverOut( node );
              }


            } ).on( 'cxttapend tapend', cxtendHandler = function( e ) {
              var cxtOk = options().cxt && e.type === 'cxttapend';
              var tapOk = drawMode && e.type === 'tapend';

              if( cxtOk || tapOk ) {

                makeEdges();

                if( sourceNode ) {
                  options().stop( sourceNode );
                  sourceNode.trigger( 'cyedgehandles.stop' );

                  options().complete( sourceNode );
                }

                resetToDefaultState();
              }

            } ).on( 'tap', 'node', tapToStartHandler = function() {
              return;
              var node = this;

              if( !sourceNode ) { // must not be active
                setTimeout( function() {
                  if( node.filter( options().handleNodes ).length === 0 ) {
                    return; // skip if node not allowed
                  }

                  clearDraws(); // clear just in case

                  var p = node.renderedPosition();
                  var h = node.renderedOuterHeight();
                  var w = node.renderedOuterWidth();

                  var hr = options().handleSize / 2 * cy.zoom();
                  var hx = p.x;
                  var hy = p.y - h / 2;

                  drawHandle( hx, hy, hr );

                  node.trigger( 'cyedgehandles.showhandle' );
                }, 16 );
              }

            } );


            data.unbind = function() {
              cy
                .off( 'mouseover', 'node', startHandler )
                .off( 'mouseover', 'node', hoverHandler )
                .off( 'mouseout', 'node', leaveHandler )
                .off( 'drag position', 'node', dragNodeHandler )
                .off( 'grab', 'node', grabNodeHandler )
                .off( 'free', 'node', freeNodeHandler )
                .off( 'cyedgehandles.forcestart', 'node', forceStartHandler )
                .off( 'remove', 'node', removeHandler )
                .off( 'cxttapstart', 'node', cxtstartHandler )
                .off( 'cxttapend', cxtendHandler )
                .off( 'cxtdrag', cxtdragHandler )
                .off( 'cxtdragover', 'node', cxtdragoverHandler )
                .off( 'cxtdragout', 'node', cxtdragoutHandler )
                .off( 'tap', 'node', tapToStartHandler );

              cy.unbind( 'zoom pan', transformHandler );

              $( window ).off( 'resize', winResizeHandler );

              $container
                .off( 'cyedgehandles.resize', ctrResizeHandler )
                .off( 'cyedgehandles.drawon', ctrDrawonHandler )
                .off( 'cyedgehandles.drawoff', ctrDrawoffHandler );
            };
          } );

          $container.data( 'cyedgehandles', data );
        },

        start: function( id ) {
          var $container = $( this );

          cy.ready( function( e ) {
            cy.$( '#' + id ).trigger( 'cyedgehandles.forcestart' );
          } );
        }
      };

      if( functions[ fn ] ) {
        return functions[ fn ].apply( container, Array.prototype.slice.call( arguments, 1 ) );
      } else if( typeof fn == 'object' || !fn ) {
        return functions.init.apply( container, arguments );
      } else {
        console.error( 'No such function `' + fn + '` for edgehandles' );
      }
    };

    $$( 'core', 'edgehandles', edgehandles );

  };

  if( typeof module !== 'undefined' && module.exports ) { // expose as a commonjs module
    module.exports = register;
  }

  if( typeof define !== 'undefined' && define.amd ) { // expose as an amd/requirejs module
    define( 'cytoscape-edgehandles', function() {
      return register;
    } );
  }

  if( $$ ) { // expose to global cytoscape (i.e. window.cytoscape)
    register( $$ );
  }

} )( typeof cytoscape !== 'undefined' ? cytoscape : null );
