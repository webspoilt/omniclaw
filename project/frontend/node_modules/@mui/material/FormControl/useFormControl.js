"use strict";
'use client';

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault").default;
var _interopRequireWildcard = require("@babel/runtime/helpers/interopRequireWildcard").default;
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = useFormControl;
exports.useFormControlState = useFormControlState;
var React = _interopRequireWildcard(require("react"));
var _FormControlContext = _interopRequireDefault(require("./FormControlContext"));
function useFormControl() {
  return React.useContext(_FormControlContext.default);
}
function useFormControlState({
  props,
  states
}) {
  const muiFormControl = React.useContext(_FormControlContext.default);
  const result = {};
  states.forEach(state => {
    const value = props[state];
    result[state] = value === undefined && muiFormControl ? muiFormControl[state] : value;
  });
  return [result, muiFormControl];
}