import { EventHandlers } from "../types/index.js";
/**
 * Extracts event handlers from a given object.
 * A prop is considered an event handler if it is a function and its name starts with `on`.
 *
 * @param object An object to extract event handlers from.
 */
declare function extractEventHandlers(object: Record<string, any> | undefined): EventHandlers;
export default extractEventHandlers;