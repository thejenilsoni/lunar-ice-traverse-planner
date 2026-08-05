# Data integration guide

## Official Chandrayaan-2 sources

Chandrayaan-2 public science products are distributed through the ISRO Science Data Archive / PRADAN portal in PDS4 form. Relevant payload categories include:

| Payload | Planning use |
| --- | --- |
| DFSAR | L/S-band radar, polarimetry, CPR, DOP, roughness and dielectric context |
| TMC-2 | Stereo imagery and digital elevation products for slope and geomorphology |
| OHRC | Very-high-resolution optical inspection of candidate landing and traverse regions |
| IIRS | Mineralogical and hydroxyl/water context |
| SPICE | Geometry, timing and coordinate transformations |

Portal: `https://pradan.issdc.gov.in/ch2/`

Instrument overview: `https://www.isro.gov.in/ISRO_EN/Chandrayaan2_science.html`

## Data-use boundary

PRADAN data remain the property of ISRO and include acknowledgement, copyright and use conditions. Review the portal terms before downloading, redistributing or publishing derived products. Do not commit restricted or large raw products to this repository.

## Canonical grid contract

The processing layer expects co-registered arrays for elevation, slope, normalized roughness, illumination, permanent shadow, surface temperature, L/S-band CPR, degree of polarization, radar coherence, hydration context and communication visibility.

Each production scene should preserve product IDs, acquisition time, coordinate reference, incidence angle, resolution, calibration version, quality flags and processing provenance.

## Demonstration scene

Run `make demo` to generate a fixed-seed JSON product. It is intentionally synthetic and contains known ice deposits and rough-rock confounders for software testing.
