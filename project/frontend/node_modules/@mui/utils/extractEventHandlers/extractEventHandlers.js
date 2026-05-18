"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault").default;
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
var _isEventHandler = _interopRequireDefault(require("@mui/utils/isEventHandler"));
/**
 * Extracts event handlers from a given object.
 * A prop is considered an event handler if it is a function and its name starts with `on`.
 *
 * @param object An object to extract event handlers from.
 */
function extractEventHandlers(object) {
  if (object === undefined) {
    return {};
  }
  const result = {};
  for (const prop of Object.keys(object)) {
    if ((0, _isEventHandler.default)(prop, object[prop])) {
      result[prop] = object[prop];
    }
  }
  return result;
}
var _default = exports.default = extractEventHandlers;