# WCAG 2.1 AA quick notes (written in plain language for this project)

These notes summarize common WCAG 2.1 Level A and AA success criteria for a university
web team. They are a study aid, not the official standard. For the official text, see
the W3C WCAG 2.1 recommendation at w3.org/TR/WCAG21.

## 1.1.1 Non-text Content (Level A)
Every meaningful image, icon or graphic needs a text alternative that serves the same purpose.
In HTML this is usually the alt attribute. Describe the purpose, not just the appearance: a
magnifying-glass icon on a search button should have alt text like "Search", not "magnifying glass".
Decorative images that add no information should use an empty alt attribute (alt="") so screen
readers skip them. An image with no alt attribute at all is a failure, because some screen readers
then read the file name. Images of text should be avoided; if used, the alt text must include the same text.
Complex images such as charts need a short alt text plus a longer description nearby.

## 1.3.1 Info and Relationships (Level A)
Structure that is visible on screen must also exist in the code. Use real headings (h1 to h6) in a
logical order without skipping levels, real lists (ul, ol), and data tables with header cells (th)
and captions. Form fields must be connected to their labels. Do not use bold text or font size alone
to create headings, because screen reader users navigate pages by heading level.

## 1.4.3 Contrast (Minimum) (Level AA)
Normal text needs a contrast ratio of at least 4.5 to 1 against its background. Large text (about
18 point regular or 14 point bold and larger) needs at least 3 to 1. Placeholder text, disabled
controls and text over images often fail. Logos and purely decorative text are exempt.

## 1.4.11 Non-text Contrast (Level AA)
Interface parts such as input borders, buttons, focus indicators and meaningful icons need a
contrast ratio of at least 3 to 1 against adjacent colors, so people with low vision can find them.

## 2.1.1 Keyboard (Level A)
All functionality must work with a keyboard alone, without requiring a mouse. Users should be able to
reach links, buttons, menus and form fields with Tab and activate them with Enter or Space. Custom
widgets built from div elements often fail unless they add keyboard support and ARIA roles.

## 2.4.2 Page Titled (Level A)
Every page needs a title element that describes its topic or purpose, such as "Student Organizations
- School of Business - USC Aiken". The title is the first thing screen readers announce and appears
on browser tabs.

## 2.4.4 Link Purpose (In Context) (Level A)
The purpose of each link should be clear from the link text, or from the link text together with its
surrounding sentence. Avoid vague text such as "click here", "read more" or "learn more" on its own.
Links that contain only an image need alt text on the image that describes the destination. Links
with no text at all are announced only as "link".

## 2.4.7 Focus Visible (Level AA)
When a user tabs through a page, the element with keyboard focus must be visibly highlighted. Removing
the browser focus outline with CSS (outline: none) without providing a replacement is a common failure.

## 3.1.1 Language of Page (Level A)
The html element must declare the main language of the page with the lang attribute, for example
lang="en". Screen readers use it to choose the correct pronunciation rules.

## 3.3.2 Labels or Instructions (Level A)
Form fields need visible labels or instructions so users know what to enter. Connect a label to its
field with the for and id attributes, or wrap the field inside the label. Placeholder text alone is
not a label because it disappears when the user types. Required fields and expected formats, such as a
date format, should be explained.

## 4.1.1 Parsing (Level A)
In WCAG 2.1, markup should not contain errors that confuse assistive technology, such as duplicate id
values. Duplicate ids break label connections and ARIA references. Note that WCAG 2.2 marks this
criterion as obsolete, but unique ids remain good practice.

## 4.1.2 Name, Role, Value (Level A)
Every interactive element needs an accessible name, a role and a state that assistive technology can
read. A button that contains only an icon needs a text label or an aria-label. Custom controls must
expose their role (for example role="switch") and state (for example aria-checked).

## Section 508 and WCAG
Section 508 is the US federal law that requires federal agencies to make their information and
communication technology accessible. The revised Section 508 standards incorporate WCAG 2.0 Level A
and AA by reference, so meeting WCAG 2.0 AA, and therefore WCAG 2.1 AA, covers the web content
requirements. Many public universities follow WCAG 2.1 AA as their standard.

## VPAT (Voluntary Product Accessibility Template)
A VPAT is a document a vendor fills out to describe how well its product meets accessibility standards
such as WCAG and Section 508. The completed document is often called an Accessibility Conformance
Report (ACR). Universities review VPATs during procurement to judge accessibility risks before buying
software, and should check that VPATs are recent and renewed when products change.
