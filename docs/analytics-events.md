# RackMath Analytics Events

This document defines the website-side analytics events emitted by the static RackMath SEO site.

Events are pushed to `window.dataLayer`, dispatched as `rackmath:{event}` browser events, and forwarded to `gtag` or `plausible` when either is present.

## Website Events

| Event | Trigger | Important fields |
| --- | --- | --- |
| `app_deeplink_clicked` | Any click to `https://www.rackmath.app` | `destination`, `destination_path`, `label`, `source_page`, `content_group`, `primary_event`, `seo_source`, `seo_tool`, `seo_template`, `seo_program`, `seo_persona`, `seo_feature` |
| `signup_started` | Website app link with “Try free” label | Same fields as app deep-link clicks |
| `tool_completed` | Free tool result calculated or preview generated | `tool`, tool-specific inputs/results, `source_page`, `content_group` |
| `template_started` | Workout or program CTA clicked | Same fields as app deep-link clicks |

## App-Side Events To Connect

These cannot be completed by the static website alone and should be emitted inside the RackMath app or billing flow:

| Event | Where it should fire |
| --- | --- |
| `signup_completed` | After account creation completes |
| `first_workout_completed` | After the user's first logged workout is saved |
| `trial_started` | After a trial is activated |
| `subscription_started` | After a paid subscription begins |

## Notes

- Every event includes `source_page`, `content_group`, and `timestamp`.
- SEO app links preserve query parameters such as `source=seo`, `tool`, `template`, `program`, `persona`, and `feature`.
- Links with a specific primary event, such as `template_started`, also emit `app_deeplink_clicked` for funnel reporting.
