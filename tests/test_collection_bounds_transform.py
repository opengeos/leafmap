"""Collection bounds must use the same coordinate space as their members."""

from copy import deepcopy

import pytest

from leafmap.common import get_bounds, get_center


class Transform:
    """Small affine-compatible transform with no optional test dependency."""

    def __init__(self, sx=10, sy=-10, tx=100, ty=200):
        self.sx, self.sy, self.tx, self.ty = sx, sy, tx, ty

    def __mul__(self, point):
        x, y = point
        return self.sx * x + self.tx, self.sy * y + self.ty


def polygon(x=0, y=0):
    return {
        "type": "Polygon",
        "coordinates": [[[x, y], [x + 2, y], [x + 2, y + 3], [x, y + 3], [x, y]]],
    }


def feature(geometry):
    return {"type": "Feature", "properties": {}, "geometry": geometry}


def collection(geometries, kind):
    if kind == "FeatureCollection":
        return {"type": kind, "features": [feature(g) for g in geometries]}
    return {"type": kind, "geometries": geometries}


@pytest.mark.parametrize("kind", ["FeatureCollection", "GeometryCollection"])
@pytest.mark.parametrize("north_up", [True, False])
@pytest.mark.parametrize("sy", [-10, 10])
def test_single_collection_matches_transformed_member(kind, north_up, sy):
    geom = polygon()
    data = collection([geom], kind)
    before = deepcopy(data)
    transform = Transform(sy=sy)
    expected = (100, 200, 120, 170) if sy < 0 else (100, 230, 120, 200)
    assert get_bounds(geom, north_up=north_up, transform=transform) == expected
    assert get_bounds(feature(geom), north_up=north_up, transform=transform) == expected
    assert get_bounds(data, north_up=north_up, transform=transform) == expected
    assert get_center(data, north_up=north_up, transform=transform) == (
        110,
        185 if sy < 0 else 215,
    )
    assert data == before


@pytest.mark.parametrize("kind", ["FeatureCollection", "GeometryCollection"])
@pytest.mark.parametrize("north_up", [True, False])
def test_disjoint_members_aggregate_extrema_in_transformed_space(kind, north_up):
    data = collection([polygon(), polygon(4, 5)], kind)
    assert get_bounds(data, north_up=north_up, transform=Transform()) == (
        100,
        200,
        160,
        120,
    )
    assert get_center(data, north_up=north_up, transform=Transform()) == (130, 160)


@pytest.mark.parametrize("outer", ["FeatureCollection", "GeometryCollection"])
def test_nested_collections_keep_transform(outer):
    inner = "GeometryCollection"
    # GeometryCollection is a valid geometry inside either wrapper.
    data = collection([collection([polygon(), polygon(4, 5)], inner)], outer)
    assert get_bounds(data, transform=Transform()) == (100, 200, 160, 120)


@pytest.mark.parametrize("kind", ["FeatureCollection", "GeometryCollection"])
@pytest.mark.parametrize("north_up", [True, False])
def test_untransformed_orientation_is_unchanged(kind, north_up):
    data = collection([polygon(), polygon(4, 5)], kind)
    assert get_bounds(data, north_up=north_up) == (
        (0, 0, 6, 8) if north_up else (0, 8, 6, 0)
    )


def test_identity_transform_still_uses_transformed_geometry_order():
    geom = polygon()
    assert get_bounds(
        collection([geom], "FeatureCollection"), transform=Transform(1, 1, 0, 0)
    ) == (0, 3, 2, 0)


def test_negative_x_scale_aggregates_normalized_x_extrema():
    data = collection([polygon(), polygon(4, 5)], "GeometryCollection")
    assert get_bounds(data, transform=Transform(sx=-10)) == (40, 200, 100, 120)


@pytest.mark.parametrize("kind", ["FeatureCollection", "GeometryCollection"])
def test_explicit_bbox_shortcut_preserved(kind):
    data = collection([polygon()], kind)
    data["bbox"] = [-1, -2, 3, 4]
    assert get_bounds(data, transform=Transform()) == (-1, -2, 3, 4)


def test_shear_transform_uses_all_vertices_and_member_extrema():
    class Shear:
        def __mul__(self, point):
            x, y = point
            return 100 + 2 * x + 3 * y, 200 + 4 * x - 5 * y

    data = collection([polygon(), polygon(4, 5)], "FeatureCollection")
    assert get_bounds(data, transform=Shear()) == (100, 208, 136, 176)


def test_member_explicit_bbox_keeps_existing_shortcut():
    geom = polygon()
    geom["bbox"] = [-1, -2, 3, 4]
    data = collection([geom], "GeometryCollection")
    assert get_bounds(geom, transform=Transform()) == (-1, -2, 3, 4)
    # Members are bounded in transformed space, so their raw bbox is ignored.
    assert get_bounds(data, transform=Transform()) == (100, 200, 120, 170)


@pytest.mark.parametrize("kind", ["FeatureCollection", "GeometryCollection"])
def test_mixed_member_bbox_stays_in_transformed_space(kind):
    with_bbox = polygon()
    with_bbox["bbox"] = [0, 0, 2, 3]
    data = collection([with_bbox, polygon(4, 5)], kind)
    expected = get_bounds(
        collection([polygon(), polygon(4, 5)], kind), transform=Transform()
    )
    assert get_bounds(data, transform=Transform()) == expected
    assert get_center(data, transform=Transform()) == (130, 160)


@pytest.mark.parametrize("transform", [None, Transform()])
def test_null_geometry_features_are_skipped(transform):
    data = collection([polygon(), polygon(4, 5)], "FeatureCollection")
    data["features"].insert(1, feature(None))
    expected = get_bounds(
        collection([polygon(), polygon(4, 5)], "FeatureCollection"),
        transform=transform,
    )
    assert get_bounds(data, transform=transform) == expected


def test_collection_without_located_geometries_raises():
    data = collection([None], "FeatureCollection")
    with pytest.raises(ValueError, match="located geometries"):
        get_bounds(data)
