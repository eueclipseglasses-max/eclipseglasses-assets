# EclipseGlasses Cloudflare Worker setup

## Required bindings

Configure these on the Cloudflare Worker before using quote requests:

- **D1 database binding:** variable name `DB`
- **Worker secret:** `ADMIN_PASSWORD` (a strong, unique password)
- **Email service binding:** `EMAIL` if email notifications should be sent. The quote is saved to D1 even if email delivery fails.

## Create the quote table

Run `schema.sql` against the D1 database bound to this Worker. The public quote endpoint inserts records into the `quotes` table and the authenticated `/admin` page reads from it.

## Admin

Open `https://YOUR-DOMAIN/admin`. HTTP Basic Authentication uses username `admin` and the password stored in the `ADMIN_PASSWORD` secret. Do not put the password in source code or commit it to Git.

## Shopify

The current storefront's cart/checkout is not connected to Shopify; it uses a mailto flow. Do not represent orders or payments as Shopify-backed until Shopify credentials, a store domain, products/prices, and the desired checkout flow have been configured and tested. Keep private Shopify credentials in Worker secrets, never in browser JavaScript.
