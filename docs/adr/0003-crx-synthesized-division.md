# CRX: a synthesized Division for continuing-resolution extras

CRX is a LawSearch Division that does not correspond to a single Bill Division. It aggregates Bill Divisions covering continuing appropriations, extenders, Homeland Security, and miscellaneous matter — currently nine Bill Divisions across two Public Laws for FY2026.

## Why

Several of the bundled Bill Divisions are small or topically narrow on their own (e.g. Health Extenders, Veterans Affairs Extenders, Authorizing Extenders and Technical Corrections). Treating each as a standalone Division would create routing targets too thin to reliably select and would split related content across stores. CRX gives them a single retrieval bucket whose Routing Alias enumerates their topics.

## Trade-off accepted

CRX is the one place where Division and Bill Division diverge, and the [`FY2026_SOURCE_PARTS`](../../app/core/config.py) manifest exists largely to keep that mapping explicit. Citations into CRX content lose the cleaner "this came from Public Law X, Division Y" narrative that other Divisions have for free. Worth it for routing quality.
