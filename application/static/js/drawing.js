const pSBC=(p,c0,c1,l)=>{
	let r,g,b,P,f,t,h,m=Math.round,a=typeof(c1)=="string";
	if(typeof(p)!="number"||p<-1||p>1||typeof(c0)!="string"||(c0[0]!='r'&&c0[0]!='#')||(c1&&!a))return null;
	h=c0.length>9,h=a?c1.length>9?true:c1=="c"?!h:false:h,f=pSBC.pSBCr(c0),P=p<0,t=c1&&c1!="c"?pSBC.pSBCr(c1):P?{r:0,g:0,b:0,a:-1}:{r:255,g:255,b:255,a:-1},p=P?p*-1:p,P=1-p;
	if(!f||!t)return null;
	if(l)r=m(P*f.r+p*t.r),g=m(P*f.g+p*t.g),b=m(P*f.b+p*t.b);
	else r=m((P*f.r**2+p*t.r**2)**0.5),g=m((P*f.g**2+p*t.g**2)**0.5),b=m((P*f.b**2+p*t.b**2)**0.5);
	a=f.a,t=t.a,f=a>=0||t>=0,a=f?a<0?t:t<0?a:a*P+t*p:0;
	if(h)return"rgb"+(f?"a(":"(")+r+","+g+","+b+(f?","+m(a*1000)/1000:"")+")";
	else return"#"+(4294967296+r*16777216+g*65536+b*256+(f?m(a*255):0)).toString(16).slice(1,f?undefined:-2)
};

pSBC.pSBCr=(d)=>{
	const i=parseInt;
	let n=d.length,x={};
	if(n>9){
		const [r, g, b, a] = (d = d.split(','));
	        n = d.length;
		if(n<3||n>4)return null;
		x.r=i(r[3]=="a"?r.slice(5):r.slice(4)),x.g=i(g),x.b=i(b),x.a=a?parseFloat(a):-1
	}else{
		if(n==8||n==6||n<4)return null;
		if(n<6)d="#"+d[1]+d[1]+d[2]+d[2]+d[3]+d[3]+(n>4?d[4]+d[4]:"");
		d=i(d.slice(1),16);
		if(n==9||n==5)x.r=d>>24&255,x.g=d>>16&255,x.b=d>>8&255,x.a=Math.round((d&255)/0.255)/1000;
		else x.r=d>>16,x.g=d>>8&255,x.b=d&255,x.a=-1
	}return x
};

var secondaryColor = pSBC(0.3, mainColor);
var currentColor = mainColor;
var brushSize;

var canvas,ctx;
var mouseX,mouseY,moving, mouseDown=0;
var touchX,touchY;
var previousPoint;


function initControls() {
    let sizeSlider = document.getElementById("brushSize");
    brushSize = sizeSlider.value;
    sizeSlider.addEventListener("input", changeBrushSize);

    let mainColorBtn = document.getElementById("main-color")
    mainColorBtn.style.backgroundColor = mainColor;
    mainColorBtn.addEventListener("click", selectColor);

    let secondaryColorBtn = document.getElementById("secondary-color")
    secondaryColorBtn.style.backgroundColor = secondaryColor;
    secondaryColorBtn.addEventListener("click", selectColor);
}


function initCanvas() {
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
		    document.addEventListener('mouseup', mouseOrTouchUp, false);
		    canvas.addEventListener('mouseenter', mouseEnter, false);

		    // React to touch events on the canvas
		    canvas.addEventListener('touchstart', sketchpad_touchStart, false);
		    canvas.addEventListener('touchmove', sketchpad_touchMove, false);
		    canvas.addEventListener('touchend', mouseOrTouchUp, false);
		}
}


function drawLine(x, y) {
		if (previousPoint && moving) {
		    ctx.strokeStyle = currentColor;
		    ctx.beginPath();
		    ctx.moveTo(previousPoint[0],previousPoint[1]);
		    ctx.lineTo(x, y);
		    ctx.lineCap = "round";
		    ctx.lineJoin = "round";
		    ctx.lineWidth = brushSize;
		    ctx.stroke();
		    ctx.closePath();
		    ctx.fill();
		}
}


function drawDot() {
		ctx.fillStyle = currentColor;
		ctx.beginPath();
		ctx.arc(previousPoint[0], previousPoint[1], brushSize/2, 0, Math.PI*2, true);
		ctx.closePath();
		ctx.fill();
}


function sketchpad_mouseDown() {
		previousPoint = [mouseX, mouseY];
		drawDot();
		mouseDown=1;
}


function mouseOrTouchUp() {
		mouseDown=0;
		moving=0;
}


function mouseEnter(e) {
    if (mouseDown) {
        getMousePos(e);
        previousPoint = [mouseX, mouseY];
    }
}


function sketchpad_mouseMove(e) {
		getMousePos(e);

		if (mouseDown==1) {
		    drawLine(mouseX, mouseX);
		    previousPoint = [mouseX, mouseX];
		    moving=1;
		}
}

// Get the current mouse position relative to the top-left of the canvas
function getMousePos(e) {
		if (!e)
		    var e = event;

		if (e.offsetX !== undefined) {
		    mouseX = e.offsetX;
		    mouseY = e.offsetY;
		}
		else if (e.layerX !== undefined) {
		    mouseX = e.layerX;
		    mouseY = e.layerY;
		}
}

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

// Draw something when a touch start is detected
function sketchpad_touchStart() {
		getTouchPos();
		previousPoint = [touchX, touchY];
		drawDot();

		// Prevent a scrolling action as a result of this touchmove triggering.
		event.preventDefault();
		moving=1;
}

function sketchpad_touchMove(e) {
		getTouchPos(e);
		drawLine(touchX, touchY);
		previousPoint = [touchX, touchY];

		// Prevent a scrolling action as a result of this touchmove triggering.
		event.preventDefault();
}


function changeBrushSize() {
    brushSize = document.getElementById("brushSize").value;
}

function selectColor(e) {
	document.querySelectorAll('#colors-block button').forEach(
		(el) => el.classList.remove('active')
	);
  e.target.classList.add('active');
	if (this.id === "main-color") currentColor = mainColor;
	if (this.id === "secondary-color") currentColor = secondaryColor;
}


initControls();
initCanvas();