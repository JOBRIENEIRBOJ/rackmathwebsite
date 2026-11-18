import { createIndexNowHooks } from './helpers.js';

const hooks = createIndexNowHooks();

export const onPreBuild = hooks.onPreBuild;
export const onSuccess = hooks.onSuccess;
