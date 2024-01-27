/*

=========================================================
* Volt Pro - Premium Bootstrap 5 Dashboard
=========================================================

* Product Page: https://themesberg.com/product/admin-dashboard/volt-bootstrap-5-dashboard
* Copyright 2021 Themesberg (https://www.themesberg.com)

* Designed and coded by https://themesberg.com

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. Please contact us to request a removal. Contact us if you want to remove it.

*/

function CopyUrl(element) {
    var copyText = element.href;
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = copyText;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
}

function CopyUrlOnly(link, id) {
    var copyText = window.location.origin + link.link;
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = copyText;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
    var tooltip = document.getElementById(id)
    tooltip.innerHTML = "Copied!"
}

"use strict";
const d = document;
const origin = window.location.origin
d.addEventListener("DOMContentLoaded", function (event) {
    const sidebarMenu = d.getElementById('sidebarMenu');
    const mainContent = d.querySelector('.main-content');

    d.getElementById('sideBarToggler').addEventListener('click', function () {
        sidebarMenu.classList.toggle('d-lg-block');
        mainContent.classList.toggle('sidebar-open');
    });


    const swalWithBootstrapButtons = Swal.mixin({
        customClass: {
            confirmButton: 'btn btn-primary me-3',
            cancelButton: 'btn btn-gray'
        },
        buttonsStyling: false
    });

    var themeSettingsEl = document.getElementById('theme-settings');
    var themeSettingsExpandEl = document.getElementById('theme-settings-expand');

    if (themeSettingsEl) {

        var themeSettingsCollapse = new bootstrap.Collapse(themeSettingsEl, {
            show: true,
            toggle: false
        });

        if (window.localStorage.getItem('settings_expanded') === 'true') {
            themeSettingsCollapse.show();
            themeSettingsExpandEl.classList.remove('show');
        } else {
            themeSettingsCollapse.hide();
            themeSettingsExpandEl.classList.add('show');
        }

        themeSettingsEl.addEventListener('hidden.bs.collapse', function () {
            themeSettingsExpandEl.classList.add('show');
            window.localStorage.setItem('settings_expanded', false);
        });

        themeSettingsExpandEl.addEventListener('click', function () {
            themeSettingsExpandEl.classList.remove('show');
            window.localStorage.setItem('settings_expanded', true);
            setTimeout(function () {
                themeSettingsCollapse.show();
            }, 300);
        });
    }

    // options
    const breakpoints = {
        sm: 540,
        md: 720,
        lg: 960,
        xl: 1140
    };

    var sidebar = document.getElementById('sidebarMenu')
    if (sidebar && d.body.clientWidth < breakpoints.lg) {
        sidebar.addEventListener('shown.bs.collapse', function () {
            document.querySelector('body').style.position = 'fixed';
        });
        sidebar.addEventListener('hidden.bs.collapse', function () {
            document.querySelector('body').style.position = 'relative';
        });
    }

    var iconNotifications = d.querySelector('.notification-bell');
    if (iconNotifications) {
        iconNotifications.addEventListener('shown.bs.dropdown', function () {
            iconNotifications.classList.remove('unread');
        });
    }

    [].slice.call(d.querySelectorAll('[data-background]')).map(function (el) {
        el.style.background = 'url(' + el.getAttribute('data-background') + ')';
    });

    [].slice.call(d.querySelectorAll('[data-background-lg]')).map(function (el) {
        if (document.body.clientWidth > breakpoints.lg) {
            el.style.background = 'url(' + el.getAttribute('data-background-lg') + ')';
        }
    });

    [].slice.call(d.querySelectorAll('[data-background-color]')).map(function (el) {
        el.style.background = 'url(' + el.getAttribute('data-background-color') + ')';
    });

    [].slice.call(d.querySelectorAll('[data-color]')).map(function (el) {
        el.style.color = 'url(' + el.getAttribute('data-color') + ')';
    });

    //Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })


    // Popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })


    // Datepicker
    var datepickers = [].slice.call(d.querySelectorAll('[data-datepicker]'))
    var datepickersList = datepickers.map(function (el) {
        return new Datepicker(el, {
            buttonClass: 'btn'
        });
    })

    if (d.querySelector('.input-slider-container')) {
        [].slice.call(d.querySelectorAll('.input-slider-container')).map(function (el) {
            var slider = el.querySelector(':scope .input-slider');
            var sliderId = slider.getAttribute('id');
            var minValue = slider.getAttribute('data-range-value-min');
            var maxValue = slider.getAttribute('data-range-value-max');

            var sliderValue = el.querySelector(':scope .range-slider-value');
            var sliderValueId = sliderValue.getAttribute('id');
            var startValue = sliderValue.getAttribute('data-range-value-low');

            var c = d.getElementById(sliderId),
                id = d.getElementById(sliderValueId);

            noUiSlider.create(c, {
                start: [parseInt(startValue)],
                connect: [true, false],
                //step: 1000,
                range: {
                    'min': [parseInt(minValue)],
                    'max': [parseInt(maxValue)]
                }
            });
        });
    }

    if (d.getElementById('input-slider-range')) {
        var c = d.getElementById("input-slider-range"),
            low = d.getElementById("input-slider-range-value-low"),
            e = d.getElementById("input-slider-range-value-high"),
            f = [d, e];

        noUiSlider.create(c, {
            start: [parseInt(low.getAttribute('data-range-value-low')), parseInt(e.getAttribute('data-range-value-high'))],
            connect: !0,
            tooltips: true,
            range: {
                min: parseInt(c.getAttribute('data-range-value-min')),
                max: parseInt(c.getAttribute('data-range-value-max'))
            }
        }), c.noUiSlider.on("update", function (a, b) {
            f[b].textContent = a[b]
        });
    }

    if (d.querySelector('.ct-chart-sales-value')) {
        var apiEndpoint = origin + '/api/last-year-financial-summary'
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                new Chartist.Line('.ct-chart-sales-value', {
                    labels: data.last_12_months,
                    series: [
                        data.revenue_list,
                        data.profit_list
                    ]
                }, {
                    low: 0,
                    showArea: true,
                    fullWidth: true,
                    plugins: [
                        Chartist.plugins.tooltip()
                    ],
                    axisX: {
                        // On the x-axis start means top and end means bottom
                        position: 'end',
                        showGrid: true,
                    },
                    axisY: {
                        // On the y-axis start means left and end means right
                        showGrid: false,
                        showLabel: false,
                        labelInterpolationFnc: function (value) {
                            return '$' + (value / 1) + 'k';
                        }
                    }
                });
                d.getElementById('total-revenue').innerText = '৳ ' + data.total_revenue.toLocaleString();
                d.getElementById('average-growth-rate').innerText = data.average_growth_rate.toFixed(2) + '%';

                if (d.querySelector('.ct-chart-ranking')) {

                    var chart = new Chartist.Bar('.ct-chart-ranking', {
                        labels: data.last_12_months,
                        series: [
                            data.revenue_list,
                            data.advance_list,
                        ]
                    }, {
                        low: 0,
                        showArea: true,
                        plugins: [
                            Chartist.plugins.tooltip()
                        ],
                        axisX: {
                            // On the x-axis start means top and end means bottom
                            position: 'end'
                        },
                        axisY: {
                            // On the y-axis start means left and end means right
                            showGrid: false,
                            showLabel: false,
                            offset: 0
                        }
                    });

                    chart.on('draw', function (data) {
                        if (data.type === 'line' || data.type === 'area') {
                            data.element.animate({
                                d: {
                                    begin: 2000 * data.index,
                                    dur: 2000,
                                    from: data.path.clone().scale(1, 0).translate(0, data.chartRect.height()).stringify(),
                                    to: data.path.clone().stringify(),
                                    easing: Chartist.Svg.Easing.easeOutQuint
                                }
                            });
                        }
                    });

                    d.getElementById('cash-in-hand').innerText = '৳ ' + data.cash_in_hand.toLocaleString();
                    d.getElementById('net-profit').innerText = data.pct_net_profit.toFixed(2) + '%';
                    d.getElementById('gross-profit').innerText = data.pct_gross_profit.toFixed(2) + '%';
                    d.getElementById('account-receivables').innerText = data.pct_ac_receivables.toFixed(2) + '%';
                }

            })
            .catch(error => console.error('Error fetching data:', error));
    }

    if (d.querySelector('.admin-total-cols')) {
        var apiEndpoint = origin + '/api/current-month-totals'
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                d.getElementById('new-customers').innerHTML = data.customers;
                d.getElementById('new-customers-sm').innerHTML = data.customers;
                const customersGrowth = data.customers_growth.toFixed(2);
                const customersGrowthDiv = d.getElementById('customers-growth');
                customersGrowthDiv.innerHTML = data.customers_growth.toFixed(2) + "%"
                if (customersGrowth > 0) {
                    customersGrowthDiv.parentNode.classList.add('text-success')
                }
                else {
                    customersGrowthDiv.parentNode.classList.add('text-danger')
                }


                d.getElementById('new-events').innerHTML = data.events;
                d.getElementById('new-events-sm').innerHTML = data.events;
                const eventsGrowth = data.events_growth.toFixed(2);
                const eventsGrowthDiv = d.getElementById('events-growth');
                eventsGrowthDiv.innerHTML = data.events_growth.toFixed(2) + "%"
                if (eventsGrowth > 0) {
                    eventsGrowthDiv.parentNode.classList.add('text-success')
                }
                else {
                    eventsGrowthDiv.parentNode.classList.add('text-danger')
                }

                d.getElementById('revenue').innerHTML = '৳ ' + data.revenue;
                d.getElementById('revenue-sm').innerHTML = '৳ ' + data.revenue;
                const revenueGrowth = data.revenue_growth.toFixed(2);

                const revenueGrowthDiv = d.getElementById('revenue-growth');

                revenueGrowthDiv.innerHTML = data.revenue_growth.toFixed(2) + "%"
                if (revenueGrowth > 0) {
                    revenueGrowthDiv.parentNode.classList.add('text-success')
                }
                else {
                    revenueGrowthDiv.parentNode.classList.add('text-danger')
                }

            })
            .catch(error => console.error('Error fetching data:', error));



    }

    if (d.getElementById('package-splits')) {
        var apiEndpoint = origin + '/api/package-wise-revenue'
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                // Get the table body element
                const tableBody = d.getElementById('package-splits');

                // Loop through each data entry and create a table row
                data.forEach(entry => {
                    // Create a new table row
                    const row = document.createElement('tr');

                    // Populate the table row with data
                    row.innerHTML = `
                        <th class="text-gray-900" scope="row">${entry.name}</th>
                        <td class="fw-bolder text-gray-500">${entry.budget}</td>
                        <td class="fw-bolder text-gray-500">${entry.qty_sold}</td>
                        <td class="fw-bolder text-gray-500">${entry.expected_revenue}</td>
                        <td class="fw-bolder text-gray-500">${entry.total_revenue}</td>
                        <td class="fw-bolder text-gray-500">
                            <div class="d-flex ${entry.total_revenue >= entry.expected_revenue ? 'text-success' : 'text-danger'}">
                                ${((entry.total_revenue - entry.expected_revenue) / entry.expected_revenue * 100).toFixed(2)}%
                            </div>
                        </td>
                    `;

                    // Append the table row to the table body
                    tableBody.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching data:', error));

    }

    if (d.querySelector('.ct-chart-traffic-share')) {
        var data = {
            series: [70, 20, 10]
        };

        var sum = function (a, b) { return a + b };

        new Chartist.Pie('.ct-chart-traffic-share', data, {
            labelInterpolationFnc: function (value) {
                return Math.round(value / data.series.reduce(sum) * 100) + '%';
            },
            low: 0,
            high: 8,
            donut: true,
            donutWidth: 20,
            donutSolid: true,
            fullWidth: false,
            showLabel: false,
            plugins: [
                Chartist.plugins.tooltip()
            ],
        });
    }

    if (d.getElementById('teammember-bill-view')) {
        var apiEndpoint = origin + '/api/teammemberbills/get_dashboard_data'
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                console.log(data)
                d.getElementById('tmember-events-sm').innerHTML = data.tmember_events;
                d.getElementById('tmember-events').innerHTML = data.tmember_events;
                d.getElementById('tmember-prev-events').innerHTML = data.tmember_prev_events;
                d.getElementById('tmember-revenue-sm').innerHTML = '৳ ' + data.tmember_earnings.toLocaleString();
                d.getElementById('tmember-revenue').innerHTML = '৳ ' + data.tmember_earnings.toLocaleString();
                d.getElementById('tmember-claimed').innerHTML = '৳ ' + data.tmember_claimed.toLocaleString();



                // Get the table body element
                const tableBody = d.getElementById('teammember-bill-view');

                // Loop through each data entry and create a table row
                data.recent_events.forEach(entry => {
                    // Create a new table row
                    const row = document.createElement('tr');

                    // Populate the table row with data
                    row.innerHTML = `
                        <th class="text-gray-900" scope="row">${entry.client_full_name}</th>
                        <td class="fw-bolder text-gray-500">${entry.event_type_display}</td>
                        <td class="fw-bolder text-gray-500">${entry.date}</td>
                        <td class="fw-bolder text-gray-500">${entry.package_name}</td>
                        <td class="fw-bolder text-gray-500">${entry.venue}</td>
                        <td class="fw-bolder text-gray-500">
                          <a class="btn btn-outline-success btn-sm p-1" href=${origin + entry.bill_link}>Download Bill<a>
                        </td>
                    `;

                    // Append the table row to the table body
                    tableBody.appendChild(row);
                });



            })
            .catch(error => console.error('Error fetching data:', error));

    }

    if (d.getElementById('loadOnClick')) {
        d.getElementById('loadOnClick').addEventListener('click', function () {
            var button = this;
            var loadContent = d.getElementById('extraContent');
            var allLoaded = d.getElementById('allLoadedText');

            button.classList.add('btn-loading');
            button.setAttribute('disabled', 'true');

            setTimeout(function () {
                loadContent.style.display = 'block';
                button.style.display = 'none';
                allLoaded.style.display = 'block';
            }, 1500);
        });
    }

    var scroll = new SmoothScroll('a[href*="#"]', {
        speed: 500,
        speedAsDuration: true
    });

    if (d.querySelector('.current-year')) {
        d.querySelector('.current-year').textContent = new Date().getFullYear();
    }

    // Glide JS

    if (d.querySelector('.glide')) {
        new Glide('.glide', {
            type: 'carousel',
            startAt: 0,
            perView: 3
        }).mount();
    }

    if (d.querySelector('.glide-testimonials')) {
        new Glide('.glide-testimonials', {
            type: 'carousel',
            startAt: 0,
            perView: 1,
            autoplay: 2000
        }).mount();
    }

    if (d.querySelector('.glide-clients')) {
        new Glide('.glide-clients', {
            type: 'carousel',
            startAt: 0,
            perView: 5,
            autoplay: 2000
        }).mount();
    }

    if (d.querySelector('.glide-news-widget')) {
        new Glide('.glide-news-widget', {
            type: 'carousel',
            startAt: 0,
            perView: 1,
            autoplay: 2000
        }).mount();
    }

    if (d.querySelector('.glide-autoplay')) {
        new Glide('.glide-autoplay', {
            type: 'carousel',
            startAt: 0,
            perView: 3,
            autoplay: 2000
        }).mount();
    }

    // Pricing countup
    var billingSwitchEl = d.getElementById('billingSwitch');
    if (billingSwitchEl) {
        const countUpStandard = new countUp.CountUp('priceStandard', 99, { startVal: 199 });
        const countUpPremium = new countUp.CountUp('pricePremium', 199, { startVal: 299 });

        billingSwitchEl.addEventListener('change', function () {
            if (billingSwitch.checked) {
                countUpStandard.start();
                countUpPremium.start();
            } else {
                countUpStandard.reset();
                countUpPremium.reset();
            }
        });
    }

});