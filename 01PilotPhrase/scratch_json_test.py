import json
import re

content = r"""```json
{
  "task_id": 191,
  "text": "In Oxyz space, a rectangular wall ABCD with height 3m is perpendicular to the (Oxy) plane, with points A(3, 1, 0) and B(1, 4, 0) on the ground. The (Oxy) plane is the ground, and the Oz axis points upwards (1 unit = 1m). A transmitter is at M(5, 6, 5). The transmitter emits straight waves in all directions, but the wall blocks them, creating a shadow region. A particle moves at a constant speed of 0.8 m/s in the (Oxy) plane from N(-6, -4, 0) through the origin O towards the wall. Calculate the time in seconds from when the particle enters the shadow region until it hits the base of the wall, and then returns to its starting position (though the problem asks for the time interval specifically for the shadow entry to wall contact). Round the result to one decimal place.",
  "code": "import math\n\ndef solve_shadow_time(A, B, M, N, O, speed, wall_height):\n    # Wall base is segment AB. Wall is vertical.\n    # Shadow region on Oxy plane is bounded by lines projecting M through A and B\n    # Let P(x, y, 0) be a point on the ground. P is in shadow if the segment MP intersects the wall.\n    # The wall is the rectangle with vertices A, B, B', A' where A'=(3,1,3), B'=(1,4,3).\n    # A point P(x, y, 0) is in shadow if the line MP intersects the rectangle ABCD.\n    # The line MP is: X(t) = M + t(P - M). For the intersection to be on the wall, \n    # the z-coordinate must be between 0 and wall_height.\n    # z(t) = Mz + t(0 - Mz) = Mz(1 - t). \n    # 0 <= Mz(1 - t) <= wall_height => 1 - (wall_height/Mz) <= t <= 1.\n    # The intersection point Q = M + t(P - M) must lie on the segment AB in the Oxy plane.\n    # Let Q_xy = (Mx + t(Px - Mx), My + t(Py - My)). Q_xy must be on segment AB.\n    # The shadow boundary on the ground is the projection of the top edge A'B' from M.\n    # A' = (Ax, Ay, wall_height), B' = (Bx, By, wall_height).\n    # Line MA': P = M + k(A' - M). For z=0: 5 + k(3-5) = 0 is wrong. \n    # Mz + k(wall_height - Mz) = 0 => k = -Mz / (wall_height - Mz).\n    # Let k_top = M[2] / (M[2] - wall_height).\n    # Projection of A' on Oxy: P_A = M_xy + k_top * (A'_xy - M_xy)\n    # Projection of B' on Oxy: P_B = M_xy + k_top * (B'_xy - M_xy)\n    # The shadow region is the area bounded by lines PA, PB and the segment AB.\n    \n    # Particle path: N to O to wall. Line NO: P(s) = N + s(O - N) / |O-N|\n    # N = (-6, -4, 0), O = (0, 0, 0). Direction vector v = (6, 4, 0) / sqrt(52).\n    # Path is the ray from N passing through O: P(t) = (6t, 4t, 0) for t >= -1.\n    # The particle enters the shadow when it crosses the line P_A P_B or the lines MA, MB.\n    # Actually, the shadow is the region 'behind' the wall relative to M.\n    # A point P is in shadow if the segment MP intersects the rectangle.\n    # The boundary of the shadow on the ground is the segment P_A P_B and the rays from P_A and P_B\n    # passing through A and B respectively.\n    \n    # Let's find the intersection of the path P(t) = (6t, 4t, 0) with the shadow boundaries.\n    # Path: x = 1.5y. \n    # Wall base AB: line through (3,1) and (1,4). Eq: (y-1)/(x-3) = (4-1)/(1-3) = 3/-2 => 2y-2 = -3x+9 => 3x+2y=11.\n    # Intersection of path (6t, 4t) and wall AB: 3(6t) + 2(4t) = 11 => 26t = 11 => t_wall = 11/26.\n    # Point of contact W = (6*11/26, 4*11/26) = (33/13, 22/13).\n    # Shadow boundary: The line connecting P_A and P_B.\n    # P_A = M_xy + (Mz/(Mz-wall_height)) * (A_xy - M_xy)\n    # P_A = (5, 6) + (5/(5-3)) * (3-5, 1-6) = (5, 6) + 2.5 * (-2, -5) = (0, -6.5)\n    # P_B = (5, 6) + 2.5 * (-4, -2) = (5, 6) + 2.5 * (-4, -2) = (-5, 1)\n    # Line P_A P_B: (y - (-6.5)) / (x - 0) = (1 - (-6.5)) / (-5 - 0) = 7.5 / -5 = -1.5\n    # y + 6.5 = -1.5x => 1.5x + y = -6.5\n    # Intersection of path (6t, 4t) and P_A P_B: 1.5(6t) + 4t = -6.5 => 9t + 4t = -6.5 => 13t = -6.5 => t_shadow = -0.5.\n    # Point of entry S = (6*-0.5, 4*-0.5) = (-3, -2).\n    # Distance S to W: dist = sqrt((33/13 - (-3))^2 + (22/13 - (-2))^2)\n    # dist = sqrt((33/13 + 39/13)^2 + (22/13 + 26/13)^2) = sqrt((72/13)^2 + (48/13)^2)\n    # dist = (1/13) * sqrt(72^2 + 48^2) = (24/13) * sqrt(3^2 + 2^2) = (24/13) * sqrt(13) = 24/sqrt(13).\n    # Time = dist / speed = (24/sqrt(13)) / 0.8 = 30 / sqrt(13).\n    \n    # Generalizing for parameters:\n    mx, my, mz = M\n    ax, ay, az = A\n    bx, by, bz = B\n    nx, ny, nz = N\n    ox, oy, oz = O\n    \n    k_top = mz / (mz - wall_height)\n    pax, pay = mx + k_top * (ax - mx), my + k_top * (ay - my)\n    pbx, pby = mx + k_top * (bx - mx), my + k_top * (by - my)\n    \n    # Path line: P(t) = O + t(O - N) / |O-N| is not quite right. \n    # Let's use P(t) = (ox + t*dx, oy + t*dy) where (dx, dy) is unit vector from N to O.\n    dx, dy = ox - nx, oy - ny\n    mag = math.sqrt(dx*dx + dy*dy)\n    dx, dy = dx/mag, dy/mag\n    \n    # Path: x = ox + t*dx, y = oy + t*dy. We need t relative to N, so P(s) = N + s*(dx, dy).\n    # Path: x = nx + s*dx, y = ny + s*dy.\n    # Intersection with wall AB: (x-ax)(by-ay) - (y-ay)(bx-ax) = 0\n    # (nx + s*dx - ax)(by-ay) - (ny + s*dy - ay)(bx-ax) = 0\n    # s * [dx(by-ay) - dy(bx-ax)] = (ax-nx)(by-ay) - (ay-ny)(bx-ax)\n    denom_wall = dx * (by - ay) - dy * (bx - ax)\n    s_wall = ((ax - nx) * (by - ay) - (ay - ny) * (bx - ax)) / denom_wall\n    \n    # Intersection with P_A P_B: (x-pax)(pby-pay) - (y-pay)(pbx-pax) = 0\n    # (nx + s*dx - pax)(pby-pay) - (ny + s*dy - pay)(pbx-pax) = 0\n    # s * [dx(pby-pay) - dy(pbx-pax)] = (pax-nx)(pby-pay) - (pay-ny)(pbx-pax)\n    denom_shadow = dx * (pby - pay) - dy * (pbx - pax)\n    s_shadow = ((pax - nx) * (pby - pay) - (pay - ny) * (pbx - pax)) / denom_shadow\n    \n    dist = abs(s_wall - s_shadow)\n    return round(dist / speed, 1)\n\n# The problem asks for time from entering shadow to hitting wall.\n# The \"return to original position\" part in the Vietnamese text is slightly ambiguous\n# but usually refers to the total path or just a distractor. \n# \"Tính thời gian... từ lúc chất điểm bắt đầu đi vào vùng mất sóng đến lúc chất điểm chạm vào chân tường\"\n# This is the primary request.\n" ,
  "test_list": [
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 0.8, 3) == 8.3",
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 1.0, 3) == 6.7"
  ],
  "test_setup_code": "",
  "challenge_test_list": [
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 0.5, 3) == 13.3",
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 1.2, 3) == 5.5",
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 2.0, 3) == 3.3",
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 0.8, 2) == 10.1",
    "assert solve_shadow_time((3,1,0), (1,4,0), (5,6,5), (-6,-4,0), (0,0,0), 0.8, 4) == 6.1"
  ]
}
```"""

def parse(content):
    json_blocks = re.findall(r'\{.*\}', content, re.DOTALL)
    for block in json_blocks:
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1:
            candidate = content[first_brace:last_brace+1]
            try:
                print("Trying candidate")
                return json.loads(candidate)
            except Exception as e:
                print(f"Candidate failed: {e}")
                obj_count = 0
                for i, char in enumerate(candidate):
                    if char == '{': obj_count += 1
                    elif char == '}': obj_count -= 1
                    if obj_count == 0:
                        try:
                            print(f"Trying segment up to {i}")
                            return json.loads(candidate[:i+1])
                        except Exception as e2:
                            print(f"Segment failed: {e2}")
                            break
    return None

res = parse(content)
if res:
    print("Success!")
else:
    print("Failed!")
