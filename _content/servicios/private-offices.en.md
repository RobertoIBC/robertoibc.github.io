---
id: srv-despachos
lang: en
url: /en/private-offices/
layout: servicio
servicio: despachos
title: "Private office rental, furnished and ready | OficinasYA!"
description: "Furnished private offices ready to work from on day one: by the hour from €{{ p.despacho_hora }}/h or monthly from €{{ p.despacho_mes }}/month + VAT, in {{ g.ciudades }} cities across Spain."
h1: Private office rental
subtitle: A closed, furnished space for your exclusive use. By the hour or by the month, in {{ g.espacios }} spaces across {{ g.ciudades }} cities.
eyebrow: Private offices
service_type: Private office rental
csv_key: despachos
wa_msg: "Hello, I am interested in renting a private office"
perfiles_intro: "It is the formula used by:"
perfiles:
  - Freelancers who need a proper place to receive clients.
  - Small companies that do not want to be tied to a five-year lease.
  - Branch offices of companies based in another city.
  - Teams that grow or shrink and need their office to grow or shrink with them.
cifras:
  - { num: "{{ g.espacios }}", label: "spaces in our network" }
  - { num: "{{ g.ciudades }}", label: "cities across Spain" }
  - { num: "+{{ g.empresas }}", label: "companies work with us" }
formas:
  - titulo: By the hour
    precio: despacho_hora
    unidad: hour
    texto: "You book a furnished office for as long as you need it: a meeting with a client, an interview, a morning of focused work."
    puntos:
      - "It includes high-speed WiFi and visitor reception, and carries no commitment."
      - "It is also how virtual office clients use the physical office when they need it."
  - titulo: Monthly
    precio: despacho_mes
    unidad: month
    texto: "The office is yours: furniture, phone line, daily cleaning, maintenance and utilities included, plus your company's registered address at the centre."
    puntos:
      - "At several centres the fee also includes meeting-room hours each month; check the details of yours."
      - "In Madrid and at the centres that offer it, access is permanent, 24 hours a day, with an access-control system."
      - "The contract runs month to month, renews automatically and is cancelled with 15 to 30 days' notice depending on the centre."
formas_dato:
  num: "6 to 250 m²"
  texto: "Prices are starting prices. The final amount depends on the size of the office and the city: across the network there are offices from 6 m² for one person up to 250 m² spaces for large teams."
pasos:
  - titulo: "Call {{ g.telefono }} or write on WhatsApp"
    texto: "Tell us the city, how many people you are and whether you want it by the hour or by the month."
  - titulo: Visit the centre
    texto: "If you want to see it; if you already know it or are in a hurry, we confirm availability and price on the spot."
  - titulo: Sign and move in
    texto: "The monthly contract is signed with a deposit, no guarantees and no investment, and the office is ready the same day."
donde_dato:
  num: "8 centres"
  texto: "The eight Madrid centres also have 24-hour access."
ofertas:
  - nombre: Office by the hour
    precio: despacho_hora
    unidad: hora
    unit_code: HUR
    detalle: Only the time you use. No commitment.
  - nombre: Monthly office
    precio: despacho_mes
    unidad: mes
    unit_code: MON
    detalle: Your exclusive office, with registered address.
incluye:
  - Furnished, closed office for your exclusive use
  - High-speed WiFi
  - Phone line and furniture
  - Reception and visitor welcome at the centre
  - Daily cleaning and maintenance
  - Utilities (electricity, water, air conditioning)
  - Registered address with the monthly plan
  - Meeting-room hours included with the monthly plan at several centres
no_incluye:
  - Building work, your own furniture or prior installations
  - Computer equipment
  - Printing and catering costs
  - VAT (all prices are shown without tax)
faq:
  - q: How much does a private office cost?
    a: "By the hour, from €{{ p.despacho_hora }} plus VAT, with the furnished office, WiFi and visitor reception included. By the month, from €{{ p.despacho_mes }} plus VAT, with an exclusive office, registered address, cleaning and, at several centres, meeting-room hours included. The exact price depends on the size of the office and the centre: ask by phone or on WhatsApp."
  - q: What is the difference between the hourly and the monthly office?
    a: "The hourly office is paid for the time you use and carries no commitment: it is the option for one-off meetings or occasional work. The monthly plan gives you a fixed office for your exclusive use, with your company registered at the centre. With the monthly plan the office is yours around the clock in Madrid and at the centres with permanent access."
  - q: How long does it take to start working?
    a: "The same day. The office comes furnished, with WiFi, phone and cleaning already running, so there is no building work, no move and no installation to wait for. You confirm availability on {{ g.telefono }}, sign the contract and move in. Compared with a conventional lease, where fitting out takes months, that is the main difference."
  - q: Is there a minimum term or a deposit?
    a: "The hourly office has no minimum term. The monthly plan runs month to month, renews automatically and is cancelled with 15 to 30 days' notice depending on the centre. A deposit is paid on signing; the amount depends on the centre and the office. There are no bank guarantees and no upfront investment."
  - q: Can I use an office in another city of the network?
    a: "Yes. Monthly office clients have workstations and hot desks across the whole network, and can book offices and meeting rooms by the hour at any of the {{ g.espacios }} spaces in {{ g.ciudades }} cities. It is the usual way to meet a client in another city without opening a second office."
  - q: What office sizes are available?
    a: "From individual offices of 6 m² up to 250 m² spaces for large teams. Each centre has its own range and availability changes every month, so each city page shows the size range and it is worth confirming by phone what is free."
---

## What a private office at OficinasYA! is

A private office is a closed, furnished space for your exclusive use inside one of our business centres. You walk in, work with your team, and the rest of the building — reception, meeting rooms, common areas, cleaning, utilities — is already running.

There is no building work to do, no furniture to buy and no utilities to set up: the office is handed over ready to work from on the day you sign.

[[perfiles]]

## Two ways to rent it

[[formas]]

If what you need is not a fixed office but a few hours of office a month alongside a registered address and an answered phone line, look at [Smart Office]({{ urls['srv-oficina-virtual'] }}#smart-office): the modular formula that starts from the virtual office and adds office and meeting-room hours as each month requires.

## What is included and what is not

Everything an office needs to run is included in the fee: furniture, connectivity, phone, reception, cleaning, utilities and maintenance.

What is not included is what is yours: computer equipment, printing costs and catering for meetings, which are contracted separately. And VAT: all prices on this website are shown without tax.

[[incluye]]

## How to rent

[[pasos]]

## Where

There are private offices at all {{ g.espacios }} spaces in the network, across {{ g.ciudades }} cities: the full list, with the address, opening hours and office sizes of each centre, is on each city page.

[[donde]]
