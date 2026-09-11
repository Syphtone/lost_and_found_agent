-- Seed data for Lost & Found items table

INSERT INTO items (id, category, brand, color, location, found_time, description, verification_feature, status)
VALUES
(
    'item001',
    'headphones',
    'Sony',
    'black',
    'library',
    '16:20',
    'Black Sony wireless noise-canceling headphones with carrying case',
    'small scratch on the left earcup',
    'unclaimed'
),
(
    'item002',
    'headphones',
    'Apple',
    'white',
    'student center',
    '14:10',
    'Apple AirPods Pro with wireless charging case',
    'engraved with initials J.D. on the back of the case',
    'unclaimed'
),
(
    'item003',
    'wallet',
    'Fossil',
    'brown',
    'cafeteria',
    '12:30',
    'Brown leather bi-fold wallet containing student ID card',
    'red sticker inside the cash compartment',
    'unclaimed'
),
(
    'item004',
    'backpack',
    'North Face',
    'blue',
    'engineering building',
    '17:45',
    'Dark blue North Face Recon backpack containing notebook and pens',
    'keychain shaped like a silver basketball attached to side zipper',
    'unclaimed'
),
(
    'item005',
    'water bottle',
    'Hydro Flask',
    'black',
    'gym',
    '09:15',
    '32oz matte black Hydro Flask with straw lid',
    'dent near the bottom base and a National Park sticker',
    'unclaimed'
),
(
    'item006',
    'laptop',
    'Dell',
    'silver',
    'library 2nd floor',
    '18:00',
    '15-inch silver Dell XPS laptop with charger',
    'sticker of a green frog on the bottom case',
    'unclaimed'
)
ON CONFLICT (id) DO UPDATE SET
    category = EXCLUDED.category,
    brand = EXCLUDED.brand,
    color = EXCLUDED.color,
    location = EXCLUDED.location,
    found_time = EXCLUDED.found_time,
    description = EXCLUDED.description,
    verification_feature = EXCLUDED.verification_feature;
