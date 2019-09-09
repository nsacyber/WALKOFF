import { Component, ElementRef, ViewChild, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastrService } from 'ngx-toastr';

//import * as jsPDF from 'jspdf';
//import * as html2canvas from 'html2canvas';

import { AuthService } from '../auth/auth.service';
import { HttpClient } from '@angular/common/http';
import { ReportService } from './report.service';
import { GridsterConfig, GridType, CompactType } from 'angular-gridster2';
import { Report } from '../models/report/report';

@Component({
	selector: 'reports-component',
	templateUrl: './reports.html',
	styleUrls: ['./reports.scss'],
	providers: [AuthService],
})
export class ReportsComponent implements OnInit {
	@ViewChild('reportsMain', { static: true }) main: ElementRef;
	reportName: string;
	reportId: string;
	paramsSub: any;
	activeIFrame: any;

	options: GridsterConfig;
	report: Report;

	gridRows = 0;
	gridColumns = 8;
	gridColSize = 125;
	gridGutterSize = 10;
	gridDefaultCols = 3;
	
	constructor(
		private route: ActivatedRoute, private toastrService: ToastrService,
		private http: HttpClient, private reportService: ReportService
	) { }

	/**
	 * On init, get our report name from the route params and grab the report.
	 */
	ngOnInit() {
		this.paramsSub = this.route.params.subscribe(params => {
			this.reportId = params.reportId;
			this.getReport().then(() => this.initGrid());
		});
	}

	initGrid() {
		this.gridRows = 0;
		this.report.widgets.forEach(item => {
			let widgetRows = item.y + item.rows;
			if (widgetRows > this.gridRows) this.gridRows = widgetRows;
		});

		this.options = {
			gridType: GridType.Fixed,
			compactType: CompactType.None,
			pushItems: true,
			draggable: {
				enabled: false
			},
			resizable: {
				enabled: false
			},
			fixedColWidth: this.gridColSize * 4 / 3,
			fixedRowHeight: this.gridColSize * 3 / 4,
			minCols: this.gridColumns,
			maxCols: this.gridColumns,
			minRows: 1,
			maxRows: this.gridRows,
			maxItemCols: this.gridColumns,
			minItemCols: 1,
			maxItemRows: this.gridRows,
			minItemRows: 1,
			defaultItemCols: this.gridDefaultCols,
			defaultItemRows: 1
		};
	}

	/**
	 * Gets the report by the name specified in the route params.
	 * Loads the report into an iframe currently.
	 */
	getReport() {
		this.clearReport();

		return this.reportService.getReportWithMetadata(this.reportId).then(savedReport => {
			(savedReport) ? this.report = savedReport : this.getCustomReport();
		})
	}

	clearReport() {
		this.report = null;
		if (this.activeIFrame) {
			this.main.nativeElement.removeChild(this.activeIFrame);
			this.activeIFrame = null
		}
	}

	getCustomReport() {
		this.http
			.get(`customreports/${this.reportName}/`, { responseType: 'text' })
			.toPromise()
			.then(data => {
				this.activeIFrame = document.createElement('iframe');
				(this.activeIFrame as any).srcdoc = data;
				this.activeIFrame.src = 'data:text/html;charset=utf-8,' + data;

				this.main.nativeElement.appendChild(this.activeIFrame);
			})
			.catch(e => this.toastrService.error(`Error retrieving report: ${e.message}`));
	}

	getGridWidth() {
		//return '900px';
		return this.gridColumns * Math.ceil(this.gridColSize * 4 / 3 + this.gridGutterSize) + this.gridGutterSize  + 'px';
	}

	getGridHeight() {
		//return '980px';
		return this.gridRows * Math.ceil(this.gridColSize * 3 / 4 + this.gridGutterSize) + this.gridGutterSize  + 'px';
	}

	savePDF() {
		return window.print();
		// var el = $('#main');//document.getElementById('grid');
		// var HTML_Width = el.width();
		// var HTML_Height = el.height();
		// var top_left_margin = 15;
		// var PDF_Width = HTML_Width + (top_left_margin * 2);
		// var PDF_Height = (PDF_Width * 1.5) + (top_left_margin * 2);
		// var canvas_image_width = HTML_Width;
		// var canvas_image_height = HTML_Height;

		// var totalPDFPages = Math.ceil(HTML_Height / PDF_Height) - 1;


		// html2canvas(el[0], { allowTaint: true }).then(function (canvas) {
		// 	canvas.getContext('2d');

		// 	console.log(canvas.height + "  " + canvas.width);


		// 	var imgData = canvas.toDataURL("image/jpeg", 1.0);
		// 	var pdf = new jsPDF('p', 'pt', [PDF_Width, PDF_Height]);
		// 	pdf.addImage(imgData, 'JPG', top_left_margin, top_left_margin, canvas_image_width, canvas_image_height);


		// 	for (var i = 1; i <= totalPDFPages; i++) {
		// 		pdf.addPage(PDF_Width, PDF_Height);
		// 		pdf.addImage(imgData, 'JPG', top_left_margin, -(PDF_Height * i) + (top_left_margin * 4), canvas_image_width, canvas_image_height);
		// 	}

		// 	pdf.save("HTML-Document.pdf");
		// });
		// html2canvas(document.getElementById('grid')).then(canvas => {
		// 	// var img = canvas.toDataURL("image/png");
		// 	// var doc = new jsPDF();
		// 	// doc.addImage(img, 'JPEG', 5, 20);
		// 	// doc.save(`${ this.reportName } - report.pdf`);

		// 	// var width = canvas.width;
		// 	// var height = canvas.height;
		// 	// var millimeters: any = {};
		// 	// millimeters.width = Math.floor(width * 0.264583);
		// 	// millimeters.height = Math.floor(height * 0.264583);

		// 	// var imgData = canvas.toDataURL(
		// 	// 	'image/png');
		// 	// var doc = new jsPDF("p", "mm", "a4");
		// 	// doc.deletePage(1);
		// 	// doc.addPage(millimeters.width, millimeters.height);
		// 	// doc.addImage(imgData, 'PNG', 0, 0);
		// 	// doc.save(`${ this.reportName } - report.pdf`);

		// 	//! MAKE YOUR PDF
		// 	var pdf = new jsPDF('p', 'pt', 'letter');

		// 	console.log(document.getElementById('grid').clientHeight)

		//     for (var i = 0; i <= document.getElementById('grid').clientHeight/980; i++) {
		//         //! This is all just html2canvas stuff
		//         var srcImg  = canvas;
		//         var sX      = 0;
		//         var sY      = 980*i; // start 980 pixels down for every new page
		//         var sWidth  = 900;
		//         var sHeight = 980;
		//         var dX      = 0;
		//         var dY      = 0;
		//         var dWidth  = 900;
		//         var dHeight = 980;

		//         var onePageCanvas = document.createElement("canvas");
		//         onePageCanvas.setAttribute('width', '900');
		//         onePageCanvas.setAttribute('height', '980');
		//         var ctx = onePageCanvas.getContext('2d');
		//         // details on this usage of this function: 
		//         // https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Using_images#Slicing
		//         ctx.drawImage(srcImg,sX,sY,sWidth,sHeight,dX,dY,dWidth,dHeight);

		//         // document.body.appendChild(canvas);
		//         var canvasDataURL = onePageCanvas.toDataURL("image/png", 1.0);

		//         // var width         = onePageCanvas.width;
		// 		// var height        = onePageCanvas.clientHeight;
		// 		var width = pdf.internal.pageSize.getWidth();
		// 		var height = pdf.internal.pageSize.getHeight();
		// 		console.log(width, height);

		//         //! If we're on anything other than the first page,
		//         // add another page
		//         if (i > 0) {
		//             pdf.addPage(612, 792); //8.5" x 11" in pts (in*72)
		//         }
		//         //! now we declare that we're working on that page
		//         pdf.setPage(i+1);
		//         //! now we add content to that page!
		//         pdf.addImage(canvasDataURL, 'JPEG', 0, 0, (width*1), (height*1));

		//     }
		//     //! after the for loop is finished running, we save the pdf.
		//     pdf.save('Test.pdf');
	//});
	}
}
