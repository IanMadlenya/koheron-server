'use strict';

var gulp = require('gulp');
var coffee = require('gulp-coffee');
var concat = require('gulp-concat');
var closureCompiler = require('gulp-closure-compiler'); // Google closure compiler

gulp.task('compile-js', function() {
    gulp.src('src/*.coffee')
    .pipe(concat('koheron-websocket-client.coffee'))
    .pipe(coffee())
    .pipe(gulp.dest('./lib'))
    .pipe(concat('koheron-websocket-client.js'))
    .pipe(closureCompiler('koheron-websocket-client.js'))
    .pipe(gulp.dest('./lib'));
});