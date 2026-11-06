export interface JurisdictionOption {
  id: string;
  group: string;
  label: string;
  scaleLabel: string;
  center: [number, number];
  zoom: number;
}

export const JURISDICTIONS: JurisdictionOption[] = [
  {
    "id": "india",
    "group": "National",
    "label": "All India \u2014 National Monitoring Grid",
    "scaleLabel": "598 Regional Zones",
    "center": [
      79.0,
      22.5
    ],
    "zoom": 4.5
  },
  {
    "id": "nagpur",
    "group": "Municipal 1 km Grids",
    "label": "Nagpur, Maharashtra (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (229 zones)",
    "center": [
      79.0882,
      21.1458
    ],
    "zoom": 11.2
  },
  {
    "id": "pune",
    "group": "Municipal 1 km Grids",
    "label": "Pune, Maharashtra (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (414 zones)",
    "center": [
      73.8567,
      18.5204
    ],
    "zoom": 11.0
  },
  {
    "id": "delhi",
    "group": "Municipal 1 km Grids",
    "label": "Delhi NCT (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (575 zones)",
    "center": [
      77.19,
      28.62
    ],
    "zoom": 10.6
  },
  {
    "id": "mumbai",
    "group": "Municipal 1 km Grids",
    "label": "Mumbai, Maharashtra (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      72.8777,
      19.076
    ],
    "zoom": 10.8
  },
  {
    "id": "bengaluru",
    "group": "Municipal 1 km Grids",
    "label": "Bengaluru, Karnataka (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (188 zones)",
    "center": [
      77.5946,
      12.9716
    ],
    "zoom": 10.8
  },
  {
    "id": "ahmedabad",
    "group": "Municipal 1 km Grids",
    "label": "Ahmedabad, Gujarat (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      72.5714,
      23.0225
    ],
    "zoom": 10.8
  },
  {
    "id": "hyderabad",
    "group": "Municipal 1 km Grids",
    "label": "Hyderabad, Telangana (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (188 zones)",
    "center": [
      78.4867,
      17.385
    ],
    "zoom": 10.8
  },
  {
    "id": "chennai",
    "group": "Municipal 1 km Grids",
    "label": "Chennai, Tamil Nadu (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      80.24,
      13.0827
    ],
    "zoom": 10.8
  },
  {
    "id": "kolkata",
    "group": "Municipal 1 km Grids",
    "label": "Kolkata, West Bengal (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      88.3639,
      22.5726
    ],
    "zoom": 10.8
  },
  {
    "id": "jaipur",
    "group": "Municipal 1 km Grids",
    "label": "Jaipur, Rajasthan (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      75.7873,
      26.9124
    ],
    "zoom": 10.8
  },
  {
    "id": "lucknow",
    "group": "Municipal 1 km Grids",
    "label": "Lucknow, Uttar Pradesh (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (169 zones)",
    "center": [
      80.9462,
      26.8467
    ],
    "zoom": 10.8
  },
  {
    "id": "bhopal",
    "group": "Municipal 1 km Grids",
    "label": "Bhopal, Madhya Pradesh (Municipal 1 km Grid)",
    "scaleLabel": "1 km Ward Grid (148 zones)",
    "center": [
      77.4126,
      23.2599
    ],
    "zoom": 10.8
  },
  {
    "id": "state_maharashtra",
    "group": "Indian States (Regional Grids)",
    "label": "Maharashtra \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (312 zones)",
    "center": [
      76.1691,
      19.6533
    ],
    "zoom": 6.4
  },
  {
    "id": "state_rajasthan",
    "group": "Indian States (Regional Grids)",
    "label": "Rajasthan \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (306 zones)",
    "center": [
      73.7166,
      26.6031
    ],
    "zoom": 6.3
  },
  {
    "id": "state_uttar_pradesh",
    "group": "Indian States (Regional Grids)",
    "label": "Uttar Pradesh \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (259 zones)",
    "center": [
      80.7063,
      26.9265
    ],
    "zoom": 6.4
  },
  {
    "id": "state_madhya_pradesh",
    "group": "Indian States (Regional Grids)",
    "label": "Madhya Pradesh \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (204 zones)",
    "center": [
      78.4244,
      23.8546
    ],
    "zoom": 6.4
  },
  {
    "id": "state_gujarat",
    "group": "Indian States (Regional Grids)",
    "label": "Gujarat \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (210 zones)",
    "center": [
      71.1733,
      22.5923
    ],
    "zoom": 6.6
  },
  {
    "id": "state_karnataka",
    "group": "Indian States (Regional Grids)",
    "label": "Karnataka \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (180 zones)",
    "center": [
      76.3513,
      14.435
    ],
    "zoom": 6.6
  },
  {
    "id": "state_tamil_nadu",
    "group": "Indian States (Regional Grids)",
    "label": "Tamil Nadu \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (151 zones)",
    "center": [
      79.8679,
      10.7632
    ],
    "zoom": 6.7
  },
  {
    "id": "state_west_bengal",
    "group": "Indian States (Regional Grids)",
    "label": "West Bengal \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (123 zones)",
    "center": [
      88.1571,
      24.164
    ],
    "zoom": 6.7
  },
  {
    "id": "state_bihar",
    "group": "Indian States (Regional Grids)",
    "label": "Bihar \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (212 zones)",
    "center": [
      85.8766,
      25.6402
    ],
    "zoom": 7.0
  },
  {
    "id": "state_telangana",
    "group": "Indian States (Regional Grids)",
    "label": "Telangana \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (225 zones)",
    "center": [
      79.1091,
      17.7721
    ],
    "zoom": 6.9
  },
  {
    "id": "state_andhra_pradesh",
    "group": "Indian States (Regional Grids)",
    "label": "Andhra Pradesh \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (180 zones)",
    "center": [
      83.1213,
      15.6319
    ],
    "zoom": 6.5
  },
  {
    "id": "state_kerala",
    "group": "Indian States (Regional Grids)",
    "label": "Kerala \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (167 zones)",
    "center": [
      76.5161,
      9.7461
    ],
    "zoom": 7.0
  },
  {
    "id": "state_odisha",
    "group": "Indian States (Regional Grids)",
    "label": "Odisha \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (148 zones)",
    "center": [
      86.051,
      19.5795
    ],
    "zoom": 6.7
  },
  {
    "id": "state_punjab",
    "group": "Indian States (Regional Grids)",
    "label": "Punjab \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (138 zones)",
    "center": [
      75.2845,
      30.7641
    ],
    "zoom": 7.3
  },
  {
    "id": "state_haryana",
    "group": "Indian States (Regional Grids)",
    "label": "Haryana \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (125 zones)",
    "center": [
      76.4311,
      28.7181
    ],
    "zoom": 7.4
  },
  {
    "id": "state_chhattisgarh",
    "group": "Indian States (Regional Grids)",
    "label": "Chhattisgarh \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (198 zones)",
    "center": [
      81.8615,
      21.5031
    ],
    "zoom": 6.7
  },
  {
    "id": "state_jharkhand",
    "group": "Indian States (Regional Grids)",
    "label": "Jharkhand \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (176 zones)",
    "center": [
      85.6138,
      23.4236
    ],
    "zoom": 7.1
  },
  {
    "id": "state_assam",
    "group": "Indian States (Regional Grids)",
    "label": "Assam \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (288 zones)",
    "center": [
      93.3966,
      26.0893
    ],
    "zoom": 6.8
  },
  {
    "id": "state_uttarakhand",
    "group": "Indian States (Regional Grids)",
    "label": "Uttarakhand \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (194 zones)",
    "center": [
      78.8367,
      30.6303
    ],
    "zoom": 7.3
  },
  {
    "id": "state_himachal_pradesh",
    "group": "Indian States (Regional Grids)",
    "label": "Himachal Pradesh \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (149 zones)",
    "center": [
      77.8391,
      32.6392
    ],
    "zoom": 7.3
  },
  {
    "id": "state_jammu_kashmir",
    "group": "Indian States (Regional Grids)",
    "label": "Jammu & Kashmir \u2014 State Thermal Grid",
    "scaleLabel": "State District Grid (232 zones)",
    "center": [
      75.8924,
      34.0031
    ],
    "zoom": 6.7
  }
];
