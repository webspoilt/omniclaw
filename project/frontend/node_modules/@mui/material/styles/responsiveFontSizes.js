"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault").default;
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = responsiveFontSizes;
var _formatMuiErrorMessage = _interopRequireDefault(require("@mui/utils/formatMuiErrorMessage"));
var _cssUtils = require("./cssUtils");
function responsiveFontSizes(themeInput, options = {}) {
  const {
    breakpoints = ['sm', 'md', 'lg'],
    disableAlign = false,
    factor = 2,
    variants = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'subtitle1', 'subtitle2', 'body1', 'body2', 'caption', 'button', 'overline']
  } = options;
  const theme = {
    ...themeInput
  };
  theme.typography = {
    ...theme.typography
  };
  const typography = theme.typography;

  // Convert between CSS lengths e.g. em->px or px->rem
  // Set the baseFontSize for your project. Defaults to 16px (also the browser default).
  const convert = (0, _cssUtils.convertLength)(typography.htmlFontSize);
  const breakpointValues = breakpoints.map(x => theme.breakpoints.values[x]);
  variants.forEach(variant => {
    const style = typography[variant];
    if (!style) {
      return;
    }
    const remFontSize = parseFloat(convert(style.fontSize, 'rem'));
    if (remFontSize <= 1) {
      return;
    }
    const maxFontSize = remFontSize;
    const minFontSize = 1 + (maxFontSize - 1) / factor;
    let {
      lineHeight
    } = style;
    if (!(0, _cssUtils.isUnitless)(lineHeight) && !disableAlign) {
      throw new Error(process.env.NODE_ENV !== "production" ? 'MUI: Unsupported non-unitless line height with grid alignment.\n' + 'Use unitless line heights instead.' : (0, _formatMuiErrorMessage.default)(6));
    }
    if (!(0, _cssUtils.isUnitless)(lineHeight)) {
      // make it unitless
      lineHeight = parseFloat(convert(lineHeight, 'rem')) / parseFloat(remFontSize);
    }
    let transform = null;
    if (!disableAlign) {
      transform = value => (0, _cssUtils.alignProperty)({
        size: value,
        grid: (0, _cssUtils.fontGrid)({
          pixels: 4,
          lineHeight,
          htmlFontSize: typography.htmlFontSize
        })
      });
    }
    const responsive = (0, _cssUtils.responsiveProperty)({
      cssProperty: 'fontSize',
      min: minFontSize,
      max: maxFontSize,
      unit: 'rem',
      breakpoints: breakpointValues,
      transform
    });

    // https://github.com/mui/material-ui/issues/40255
    // Preserve the original font size at the largest breakpoint.
    // Grid alignment can snap the max value away from the original designed size.
    if (breakpointValues.length > 0) {
      const lastBreakpoint = breakpointValues[breakpointValues.length - 1];
      responsive[`@media (min-width:${lastBreakpoint}px)`] = {
        fontSize: `${Math.round(maxFontSize * 10000) / 10000}rem`
      };
    }
    typography[variant] = {
      ...style,
      ...responsive
    };
  });
  return theme;
}