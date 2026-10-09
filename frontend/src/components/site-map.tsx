"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import type { SiteOut } from "@/lib/types";

const BAKU_CENTER: [number, number] = [40.4093, 49.8671];

export function SiteMap({
  sites,
  affectedSiteIds,
}: {
  sites: SiteOut[];
  affectedSiteIds?: Set<string>;
}) {
  const center: [number, number] =
    sites.length > 0 ? [sites[0].lat, sites[0].lng] : BAKU_CENTER;

  return (
    <MapContainer
      center={center}
      zoom={11}
      scrollWheelZoom={false}
      className="h-full w-full rounded-lg"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {sites.map((site) => {
        const isAffected = affectedSiteIds?.has(site.id) ?? false;
        const isDown = site.status === "down";
        const color = isDown ? "#ff5d6c" : "#37d08f";
        return (
          <CircleMarker
            key={site.id}
            center={[site.lat, site.lng]}
            radius={isAffected ? 9 : 6}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: isDown ? 0.9 : 0.6,
              weight: isAffected ? 3 : 1.5,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-semibold">{site.name}</div>
                <div className="text-muted-2">{site.district}</div>
                <div className="mt-1">
                  Status: <strong>{site.status}</strong>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
