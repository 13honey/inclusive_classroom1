const PSGC_API_BASE = 'https://psgc.cloud/api';

const PH_ZIP_OVERRIDES = {
    'surigao del norte|sison': '8404',
};

const PH_ADDRESS_FALLBACK_DATA = [
    {
        region: 'Caraga (Region XIII)',
        provinces: [
            {
                name: 'Agusan del Norte',
                cities: [
                    { name: 'Butuan City', zip: '8600', barangays: [] },
                    { name: 'Buenavista', zip: '8601', barangays: [] },
                    { name: 'Cabadbaran City', zip: '8605', barangays: [] },
                    { name: 'Carmen', zip: '8603', barangays: [] },
                    { name: 'Jabonga', zip: '8607', barangays: [] },
                    { name: 'Kitcharao', zip: '8609', barangays: [] },
                    { name: 'Las Nieves', zip: '8610', barangays: [] },
                    { name: 'Magallanes', zip: '8604', barangays: [] },
                    { name: 'Nasipit', zip: '8602', barangays: [] },
                    { name: 'Remedios T. Romualdez', zip: '8611', barangays: [] },
                    { name: 'Santiago', zip: '8608', barangays: [] },
                    { name: 'Tubay', zip: '8606', barangays: [] },
                ],
            },
            {
                name: 'Agusan del Sur',
                cities: [
                    { name: 'Bayugan City', zip: '8502', barangays: [] },
                    { name: 'Bunawan', zip: '8506', barangays: [] },
                    { name: 'Esperanza', zip: '8513', barangays: [] },
                    { name: 'La Paz', zip: '8508', barangays: [] },
                    { name: 'Loreto', zip: '8507', barangays: [] },
                    { name: 'Prosperidad', zip: '8500', barangays: [] },
                    { name: 'Rosario', zip: '8504', barangays: [] },
                    { name: 'San Francisco', zip: '8501', barangays: [] },
                    { name: 'San Luis', zip: '8511', barangays: [] },
                    { name: 'Santa Josefa', zip: '8512', barangays: [] },
                    { name: 'Sibagat', zip: '8503', barangays: [] },
                    { name: 'Talacogon', zip: '8510', barangays: [] },
                    { name: 'Trento', zip: '8505', barangays: [] },
                    { name: 'Veruela', zip: '8509', barangays: [] },
                ],
            },
            {
                name: 'Dinagat Islands',
                cities: [
                    { name: 'Basilisa', zip: '8413', barangays: [] },
                    { name: 'Cagdianao', zip: '8411', barangays: [] },
                    { name: 'Dinagat', zip: '8412', barangays: [] },
                    { name: 'Libjo', zip: '8414', barangays: [] },
                    { name: 'Loreto', zip: '8415', barangays: [] },
                    { name: 'San Jose', zip: '8427', barangays: [] },
                    { name: 'Tubajon', zip: '8426', barangays: [] },
                ],
            },
            {
                name: 'Surigao del Norte',
                cities: [
                    { name: 'Alegria', zip: '8425', barangays: [] },
                    { name: 'Bacuag', zip: '8408', barangays: [] },
                    { name: 'Burgos', zip: '8424', barangays: [] },
                    { name: 'Claver', zip: '8410', barangays: [] },
                    { name: 'Dapa', zip: '8417', barangays: [] },
                    { name: 'Del Carmen', zip: '8418', barangays: [] },
                    { name: 'General Luna', zip: '8419', barangays: [] },
                    { name: 'Gigaquit', zip: '8409', barangays: [] },
                    { name: 'Mainit', zip: '8407', barangays: [] },
                    { name: 'Malimono', zip: '8402', barangays: [] },
                    { name: 'Pilar', zip: '8420', barangays: [] },
                    { name: 'Placer', zip: '8405', barangays: [] },
                    { name: 'San Benito', zip: '8423', barangays: [] },
                    { name: 'San Francisco', zip: '8401', barangays: [] },
                    { name: 'San Isidro', zip: '8421', barangays: [] },
                    { name: 'Santa Monica', zip: '8422', barangays: [] },
                    {
                        name: 'Sison',
                        zip: '8404',
                        barangays: [
                            'Biyabid',
                            'Gacepan',
                            'Ima',
                            'Lower Patag',
                            'Mabuhay',
                            'Mayag',
                            'Poblacion',
                            'San Isidro',
                            'San Pablo',
                            'Tagbayani',
                            'Tinogpahan',
                            'Upper Patag',
                        ],
                    },
                    { name: 'Socorro', zip: '8416', barangays: [] },
                    { name: 'Surigao City', zip: '8400', barangays: [] },
                    { name: 'Tagana-an', zip: '8403', barangays: [] },
                    { name: 'Tubod', zip: '8406', barangays: [] },
                ],
            },
            {
                name: 'Surigao del Sur',
                cities: [
                    { name: 'Barobo', zip: '8309', barangays: [] },
                    { name: 'Bayabas', zip: '8303', barangays: [] },
                    { name: 'Bislig City', zip: '8311', barangays: [] },
                    { name: 'Cagwait', zip: '8304', barangays: [] },
                    { name: 'Cantilan', zip: '8317', barangays: [] },
                    { name: 'Carmen', zip: '8315', barangays: [] },
                    { name: 'Carrascal', zip: '8318', barangays: [] },
                    { name: 'Cortes', zip: '8313', barangays: [] },
                    { name: 'Hinatuan', zip: '8310', barangays: [] },
                    { name: 'Lanuza', zip: '8314', barangays: [] },
                    { name: 'Lianga', zip: '8307', barangays: [] },
                    { name: 'Lingig', zip: '8312', barangays: [] },
                    { name: 'Madrid', zip: '8316', barangays: [] },
                    { name: 'Marihatag', zip: '8306', barangays: [] },
                    { name: 'San Agustin', zip: '8305', barangays: [] },
                    { name: 'San Miguel', zip: '8301', barangays: [] },
                    { name: 'Tagbina', zip: '8308', barangays: [] },
                    { name: 'Tago', zip: '8302', barangays: [] },
                    { name: 'Tandag City', zip: '8300', barangays: [] },
                ],
            },
        ],
    },
];

const phAddressState = {};

function phTitleCase(value) {
    const keepUpper = ['II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX'];
    const keepLower = ['de', 'del', 'dela', 'la', 'ng', 'sa'];
    return (value || '')
        .trim()
        .replace(/\s+/g, ' ')
        .toLowerCase()
        .replace(/\b[a-z]/g, letter => letter.toUpperCase())
        .replace(/\b(?:Ii|Iii|Iv|Vi|Vii|Viii|Ix)\b/g, word => keepUpper.find(item => item.toLowerCase() === word.toLowerCase()) || word)
        .replace(/\b(?:De|Del|Dela|La|Ng|Sa)\b/g, word => keepLower.find(item => item.toLowerCase() === word.toLowerCase()) || word);
}

function phCleanBarangay(value) {
    return phTitleCase(value).replace(/^(Brgy\.?|Barangay)\s+/i, '').trim();
}

function phSetOptions(listId, values) {
    const selectId = listId.replace(/^(.+)-([^-]+)-options$/, '$1-address-$2');
    const list = document.getElementById(listId) || document.getElementById(selectId);
    if (!list) return;
    const currentValue = list.value;
    const label = list.getAttribute('data-placeholder') || list.querySelector('option[value=""]')?.textContent || 'Select';
    list.innerHTML = '';
    if (list.tagName === 'SELECT') {
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = label;
        list.appendChild(placeholder);
    }
    values.forEach(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        list.appendChild(option);
    });
    if (values.includes(currentValue)) list.value = currentValue;
}

function phNormalizeName(value) {
    return (value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function phNameTokens(value) {
    return (value || '').toLowerCase().match(/[a-z0-9]+/g) || [];
}

function phNamesMatch(a, b) {
    const left = phNormalizeName(a);
    const right = phNormalizeName(b);
    const leftTokens = phNameTokens(a);
    const rightTokens = phNameTokens(b);
    const sameTokens = leftTokens.length === rightTokens.length &&
        leftTokens.every(token => rightTokens.includes(token));
    return left === right || left.includes(right) || right.includes(left) || sameTokens;
}

function phState(prefix) {
    if (!phAddressState[prefix]) {
        phAddressState[prefix] = {
            regions: PH_ADDRESS_FALLBACK_DATA,
            provinces: [],
            cities: [],
            barangays: [],
            remote: false,
        };
    }
    return phAddressState[prefix];
}

function phNormalizeApiList(payload) {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.data)) return payload.data;
    return [];
}

async function phFetchList(path) {
    const response = await fetch(`${PSGC_API_BASE}${path}`, {cache: 'force-cache'});
    if (!response.ok) throw new Error(`PSGC request failed: ${response.status}`);
    return phNormalizeApiList(await response.json());
}

function phFallbackRegionByName(value) {
    return PH_ADDRESS_FALLBACK_DATA.find(item => phNamesMatch(item.region, value) || phNamesMatch('Region XIII Caraga', value));
}

function phFallbackProvinceByName(region, value) {
    return region?.provinces.find(item => phNamesMatch(item.name, value));
}

function phFallbackCityByName(province, value) {
    return province?.cities.find(item => phNamesMatch(item.name, value));
}

function phExactMatch(value, items, key = item => item.name) {
    const normalized = (value || '').trim().toLowerCase();
    return items.find(item => key(item).toLowerCase() === normalized);
}

function phGet(prefix, suffix) {
    return document.getElementById(`${prefix}-address-${suffix}`);
}

function phSelectedRegion(prefix) {
    const state = phState(prefix);
    const value = phGet(prefix, 'region')?.value;
    if (state.remote) return phExactMatch(value, state.regions);
    return phExactMatch(value, state.regions, item => item.region);
}

function phSelectedProvince(prefix) {
    const state = phState(prefix);
    const value = phGet(prefix, 'province')?.value;
    if (state.remote) return phExactMatch(value, state.provinces);
    const region = phSelectedRegion(prefix);
    return region ? phExactMatch(value, region.provinces) : null;
}

function phSelectedCity(prefix) {
    const state = phState(prefix);
    const value = phGet(prefix, 'city')?.value;
    if (state.remote) return phExactMatch(value, state.cities);
    const province = phSelectedProvince(prefix);
    return province ? phExactMatch(value, province.cities) : null;
}

function phCityZip(province, city) {
    if (!city) return '';
    const key = `${(province?.name || '').toLowerCase()}|${(city.name || '').toLowerCase()}`;
    return PH_ZIP_OVERRIDES[key] || city.zip || city.zip_code || '';
}

function syncPhilippineAddress(prefix) {
    const hidden = document.getElementById(`${prefix}-address`);
    const preview = document.getElementById(`${prefix}-address-preview`);
    const provinceRecord = phSelectedProvince(prefix);
    const cityRecord = phSelectedCity(prefix);
    const barangayInput = phCleanBarangay(phGet(prefix, 'barangay')?.value || '');
    const state = phState(prefix);
    const barangayMatch = (state.remote ? state.barangays : cityRecord?.barangays || [])
        .find(item => item.name ? phNamesMatch(item.name, barangayInput) : phNamesMatch(item, barangayInput));

    const line = phTitleCase(phGet(prefix, 'line')?.value || '');
    const barangay = barangayMatch?.name || barangayMatch || barangayInput;
    const city = cityRecord?.name || phTitleCase(phGet(prefix, 'city')?.value || '');
    const province = provinceRecord?.name || phTitleCase(phGet(prefix, 'province')?.value || '');
    const postalInput = phGet(prefix, 'postal');
    const postal = (postalInput?.value || '').replace(/\D/g, '').slice(0, 4) || phCityZip(provinceRecord, cityRecord);

    if (postalInput && !postalInput.value && phCityZip(provinceRecord, cityRecord)) postalInput.value = phCityZip(provinceRecord, cityRecord);
    if (postalInput && postalInput.value) postalInput.value = postal;

    const parts = [];
    if (line) parts.push(line);
    if (barangay) parts.push(`Brgy. ${barangay}`);
    if (city) parts.push(city);
    if (province) parts.push(province);
    if (postal) parts.push(postal);

    const address = parts.join(', ');
    if (hidden) hidden.value = address;
    if (preview) preview.textContent = address || 'Select a Philippine address above.';
}

async function refreshPhilippineCascade(prefix, changedField) {
    const state = phState(prefix);
    const region = phSelectedRegion(prefix);

    if (state.remote && changedField === 'region' && region?.code) {
        state.provinces = await phFetchList(`/regions/${region.code}/provinces`);
        state.cities = [];
        state.barangays = [];
    }

    phSetOptions(
        `${prefix}-province-options`,
        state.remote ? state.provinces.map(item => item.name) : (region ? region.provinces.map(item => item.name) : [])
    );

    if (changedField === 'region') {
        phGet(prefix, 'province').value = '';
        phGet(prefix, 'city').value = '';
        phGet(prefix, 'barangay').value = '';
        phGet(prefix, 'postal').value = '';
    }

    const province = phSelectedProvince(prefix);

    if (state.remote && changedField === 'province' && province?.code) {
        state.cities = await phFetchList(`/provinces/${province.code}/cities-municipalities`);
        state.barangays = [];
    }

    phSetOptions(
        `${prefix}-city-options`,
        state.remote ? state.cities.map(item => item.name) : (province ? province.cities.map(item => item.name) : [])
    );

    if (changedField === 'province') {
        phGet(prefix, 'city').value = '';
        phGet(prefix, 'barangay').value = '';
        phGet(prefix, 'postal').value = '';
    }

    const city = phSelectedCity(prefix);

    if (state.remote && changedField === 'city' && city?.code) {
        state.barangays = await phFetchList(`/cities-municipalities/${city.code}/barangays`);
    }

    phSetOptions(
        `${prefix}-barangay-options`,
        state.remote ? state.barangays.map(item => item.name) : (city ? city.barangays : [])
    );

    if (changedField === 'city') {
        phGet(prefix, 'barangay').value = '';
        phGet(prefix, 'postal').value = phCityZip(province, city);
    }

    syncPhilippineAddress(prefix);
}

async function refreshPhilippineCascadeSafely(prefix, changedField) {
    try {
        await refreshPhilippineCascade(prefix, changedField);
    } catch (error) {
        phState(prefix).remote = false;
        console.warn('PSGC cascade request failed. Keeping local fallback data.', error);
        refreshPhilippineCascade(prefix);
    }
}

function loadPhilippineAddress(prefix) {
    const hidden = document.getElementById(`${prefix}-address`);
    const raw = hidden?.value || '';
    const parts = raw.split(',').map(part => part.trim()).filter(Boolean);
    const postal = parts.length && /^\d{4}$/.test(parts[parts.length - 1]) ? parts.pop() : '';
    const province = parts.pop() || '';
    const city = parts.pop() || '';
    const barangay = phCleanBarangay(parts.pop() || '');
    const line = parts.join(', ');

    const fallbackRegion = PH_ADDRESS_FALLBACK_DATA.find(region =>
        region.provinces.some(item => phNamesMatch(item.name, province))
    ) || phFallbackRegionByName(province);
    phGet(prefix, 'region').value = fallbackRegion?.region || '';
    phGet(prefix, 'province').value = province;
    phGet(prefix, 'city').value = city;
    phGet(prefix, 'barangay').value = barangay;
    phGet(prefix, 'line').value = line;
    phGet(prefix, 'postal').value = postal;

    refreshPhilippineCascade(prefix);
}

async function phEnableRemoteAddressData(prefix) {
    const state = phState(prefix);
    const regionInput = phGet(prefix, 'region');
    const provinceInput = phGet(prefix, 'province');
    const cityInput = phGet(prefix, 'city');
    const barangayInput = phGet(prefix, 'barangay');

    try {
        const regions = await phFetchList('/regions');
        if (!regions.length) return;

        state.remote = true;
        state.regions = regions;
        phSetOptions(`${prefix}-region-options`, regions.map(item => item.name));

        const currentRegion = regionInput.value;
        const matchedRegion = regions.find(item => phNamesMatch(item.name, currentRegion));
        if (matchedRegion) {
            regionInput.value = matchedRegion.name;
            state.provinces = await phFetchList(`/regions/${matchedRegion.code}/provinces`);
            phSetOptions(`${prefix}-province-options`, state.provinces.map(item => item.name));
        }

        const matchedProvince = state.provinces.find(item => phNamesMatch(item.name, provinceInput.value));
        if (matchedProvince) {
            provinceInput.value = matchedProvince.name;
            state.cities = await phFetchList(`/provinces/${matchedProvince.code}/cities-municipalities`);
            phSetOptions(`${prefix}-city-options`, state.cities.map(item => item.name));
        }

        const matchedCity = state.cities.find(item => phNamesMatch(item.name, cityInput.value));
        if (matchedCity) {
            cityInput.value = matchedCity.name;
            state.barangays = await phFetchList(`/cities-municipalities/${matchedCity.code}/barangays`);
            phSetOptions(`${prefix}-barangay-options`, state.barangays.map(item => item.name));
            if (!phGet(prefix, 'postal').value && phCityZip(matchedProvince, matchedCity)) {
                phGet(prefix, 'postal').value = phCityZip(matchedProvince, matchedCity);
            }
        }

        const matchedBarangay = state.barangays.find(item => phNamesMatch(item.name, barangayInput.value));
        if (matchedBarangay) barangayInput.value = matchedBarangay.name;

        syncPhilippineAddress(prefix);
    } catch (error) {
        state.remote = false;
        console.warn('Using local Philippine address fallback data.', error);
    }
}

function setupPhilippineAddress(prefix, options = {}) {
    phSetOptions(`${prefix}-region-options`, PH_ADDRESS_FALLBACK_DATA.map(item => item.region));

    if (options.loadExisting) {
        loadPhilippineAddress(prefix);
    } else {
        refreshPhilippineCascade(prefix);
    }

    phEnableRemoteAddressData(prefix);

    ['region', 'province', 'city'].forEach(field => {
        phGet(prefix, field)?.addEventListener('input', () => refreshPhilippineCascadeSafely(prefix, field));
        phGet(prefix, field)?.addEventListener('change', () => refreshPhilippineCascadeSafely(prefix, field));
    });

    ['line', 'barangay', 'postal'].forEach(field => {
        phGet(prefix, field)?.addEventListener('input', () => syncPhilippineAddress(prefix));
        phGet(prefix, field)?.addEventListener('change', () => syncPhilippineAddress(prefix));
        phGet(prefix, field)?.addEventListener('blur', event => {
            if (field !== 'postal') event.target.value = field === 'barangay' ? phCleanBarangay(event.target.value) : phTitleCase(event.target.value);
            syncPhilippineAddress(prefix);
        });
    });
}
