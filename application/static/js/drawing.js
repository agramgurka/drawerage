        // Variables for referencing the canvas and 2dcanvas context
		var canvas,ctx;

		// Variables to keep track of the mouse position and left-button status
		var mouseX,mouseY,moving, mouseDown=0;

		// Variables to keep track of the touch position
		var touchX,touchY;

		var userDrawnPixels = [];

		// Get the touch position relative to the top-left of the canvas
		// When we get the raw values of pageX and pageY below, they take into account the scrolling on the page
		// but not the position relative to our target div. We'll adjust them using "target.offsetLeft" and
		// "target.offsetTop" to get the correct values in relation to the top left of the canvas.
		function getTouchPos(e) {
				if (!e)
				    var e = event;

				if(e.touches) {
				    if (e.touches.length == 1) { // Only deal with one finger
				        var touch = e.touches[0]; // Get the information for finger #1
				        touchX=touch.pageX-touch.target.offsetLeft;
				        touchY=touch.pageY-touch.target.offsetTop;
				    }
				}
		}

		// Set-up the canvas and add our event handlers after the page has loaded
		function init() {
				// Get the specific canvas element from the HTML document
				canvas = document.getElementById('drawing-canvas');

				canvas.focus();

				const maxSize = 400;
				canvas.width  = (window.innerWidth > maxSize) ? maxSize : window.innerWidth - 12*2; // margins for col-md-6
				canvas.height = (window.innerHeight > maxSize) ? maxSize : window.innerHeight;

				// If the browser supports the canvas tag, get the 2d drawing context for this canvas
				if (canvas.getContext)
				    ctx = canvas.getContext('2d');

				// Check that we have a valid context to draw on/with before adding event handlers
				if (ctx) {
				    // React to mouse events on the canvas, and mouseup on the entire document
				    canvas.addEventListener('mousedown', sketchpad_mouseDown, false);
				    canvas.addEventListener('mousemove', sketchpad_mouseMove, false);
				    canvas.addEventListener('mouseup', mouseOrTouchUp, false);

				    // React to touch events on the canvas
				    canvas.addEventListener('touchstart', sketchpad_touchStart, false);
				    canvas.addEventListener('touchmove', sketchpad_touchMove, false);
				    canvas.addEventListener('touchend', mouseOrTouchUp, false);
				}
		}

		// Draws a dot at a specific position on the supplied canvas name
		// Parameters are: A canvas context, the x position, the y position, the size of the dot
		function drawLine(ctx, x, y, size) {
				ctx.strokeStyle = drawingColor;
				ctx.beginPath();

				var n = userDrawnPixels.length;
				var point = userDrawnPixels[n-1];

				if ((n>1) && moving) {
				    var prevPoint = userDrawnPixels[n-2];
				    ctx.moveTo(prevPoint[0],prevPoint[1]);
				    ctx.lineTo(point[0], point[1]);
				} else {
				    //ctx.moveTo(point[0],point[0]);
				    //ctx.lineTo(point[0], point[1]);
				}

				ctx.lineCap = "round";
				ctx.lineJoin = "round";
				ctx.lineWidth = size;
				ctx.stroke();
				ctx.closePath();
				ctx.fill();
		}


		function drawDot(ctx, x, y, size) {
				ctx.fillStyle = drawingColor;

				// Draw a filled circle
				ctx.beginPath();
				ctx.arc(x, y, size, 0, Math.PI*2, true);
				ctx.closePath();
				ctx.fill();
		}

				// Keep track of the mouse button being pressed and draw a dot at current location
		function sketchpad_mouseDown() {

				userDrawnPixels.push([mouseX, mouseY]);
				drawDot(ctx,mouseX,mouseY,3);

				mouseDown=1;
		}


		function mouseOrTouchUp() {
				mouseDown=0;
				moving=0;
		}

		function sketchpad_mouseMove(e) {
				// Update the mouse co-ordinates when moved
				getMousePos(e);

				// Draw a dot if the mouse button is currently being pressed
				if (mouseDown==1) {
				    drawLine(ctx,mouseX,mouseY,6);
				    userDrawnPixels.push([mouseX, mouseY]);
				    moving=1;
				}
		}

		// Get the current mouse position relative to the top-left of the canvas
		function getMousePos(e) {
				if (!e)
				    var e = event;

				if (e.offsetX) {
				    mouseX = e.offsetX;
				    mouseY = e.offsetY;
				}
				else if (e.layerX) {
				    mouseX = e.layerX;
				    mouseY = e.layerY;
				}
		}

		// Draw something when a touch start is detected
		function sketchpad_touchStart() {
				getTouchPos();
				userDrawnPixels.push([touchX, touchY]);
				drawDot(ctx,touchX,touchY,3);

				// Prevent a scrolling action as a result of this touchmove triggering.
				event.preventDefault();

				moving=1;
		}

		function sketchpad_touchMove(e) {
				getTouchPos(e);
				userDrawnPixels.push([touchX, touchY]);
				drawLine(ctx,touchX,touchY,6);

				// Prevent a scrolling action as a result of this touchmove triggering.
				event.preventDefault();
		}

		init();