var gulp = require('gulp');
var ts = require('gulp-typescript');
var concat = require('gulp-concat');
var sourcemaps = require('gulp-sourcemaps');
var uglify = require('gulp-uglify');
var tsProject = ts.createProject('tsconfig.json');
 
gulp.task('ts', function () {
	var tsResult = tsProject.src()
		.pipe(tsProject());;

	return tsResult.js
		// .pipe(uglify())
		.pipe(gulp.dest('build'));
});

gulp.task('watch', function () {
	var watcher = gulp.watch('**/*.ts', ['ts']);
	watcher.on('change', function(event) {
		console.log('File ' + event.path + ' was ' + event.type + ', running tasks...');
	});
});

gulp.task('default', ['ts', 'watch']);