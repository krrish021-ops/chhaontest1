'use client';

import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Download, ChevronsUpDown } from 'lucide-react';
import type { CellSummary } from '@/lib/types';

interface RankingTableProps {
  cells: CellSummary[];
  selectedCellId: string | null;
  onRowClick: (cellId: string) => void;
}

type SortKey = 'suhii_night' | 'suhii_day' | 'frac_built' | 'frac_tree';
type SortDir = 'asc' | 'desc';

export default function RankingTable({
  cells,
  selectedCellId,
  onRowClick,
}: RankingTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('suhii_night');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [collapsed, setCollapsed] = useState(false);
  const [filter, setFilter] = useState<'all' | 'hot' | 'cool' | 'green'>('all');

  const filteredAndSorted = useMemo(() => {
    let result = [...cells];

    if (filter === 'hot') {
      result = result.filter((c) => c.suhii_night >= 3);
    } else if (filter === 'cool') {
      result = result.filter((c) => c.suhii_night < 1);
    } else if (filter === 'green') {
      result = result.filter((c) => c.frac_tree >= 0.2);
    }

    result.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      return sortDir === 'asc' ? va - vb : vb - va;
    });

    return result.slice(0, 30);
  }, [cells, sortKey, sortDir, filter]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const handleExportCSV = () => {
    const headers = ['cell_id', 'lat', 'lon', 'suhii_night', 'suhii_day', 'frac_built', 'frac_tree', 'frac_water'];
    const rows = cells.map((c) => headers.map((h) => c[h as keyof CellSummary]).join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nagpur_zones.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    /* NO ABSOLUTE POSITIONING - Managed by parent in page.tsx */
    <div
      className={`pointer-events-auto transition-all duration-300 ${
        collapsed ? 'translate-y-[calc(100%-40px)]' : ''
      }`}
    >
      <div className="mx-3 mb-3 bg-slate-900/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-700 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="text-slate-400 hover:text-white transition-all"
            >
              {collapsed ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            <div className="text-xs font-semibold text-white uppercase tracking-wider">
              Nagpur Zone Rankings
            </div>
            <div className="text-xs text-slate-500">
              ({filteredAndSorted.length} of {cells.length} zones)
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter chips */}
            <div className="flex gap-1">
              <FilterChip active={filter === 'all'} onClick={() => setFilter('all')}>
                All
              </FilterChip>
              <FilterChip active={filter === 'hot'} onClick={() => setFilter('hot')}>
                🔥 Hot (&gt;3°C)
              </FilterChip>
              <FilterChip active={filter === 'cool'} onClick={() => setFilter('cool')}>
                ❄️ Cool
              </FilterChip>
              <FilterChip active={filter === 'green'} onClick={() => setFilter('green')}>
                🌳 High Canopy
              </FilterChip>
            </div>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 hover:text-white transition-all"
            >
              <Download className="w-3 h-3" />
              CSV
            </button>
          </div>
        </div>

        {!collapsed && (
          <div className="max-h-[240px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-900 z-10">
                <tr className="border-b border-slate-800">
                  <th className="text-left px-4 py-2 text-slate-500 font-medium">Zone ID</th>
                  <SortHeader
                    label="Night SUHII"
                    active={sortKey === 'suhii_night'}
                    dir={sortDir}
                    onClick={() => handleSort('suhii_night')}
                  />
                  <SortHeader
                    label="Day SUHII"
                    active={sortKey === 'suhii_day'}
                    dir={sortDir}
                    onClick={() => handleSort('suhii_day')}
                  />
                  <SortHeader
                    label="Concrete"
                    active={sortKey === 'frac_built'}
                    dir={sortDir}
                    onClick={() => handleSort('frac_built')}
                  />
                  <SortHeader
                    label="Tree Canopy"
                    active={sortKey === 'frac_tree'}
                    dir={sortDir}
                    onClick={() => handleSort('frac_tree')}
                  />
                </tr>
              </thead>
              <tbody>
                {filteredAndSorted.map((cell) => {
                  const isSelected = cell.cell_id === selectedCellId;
                  return (
                    <tr
                      key={cell.cell_id}
                      onClick={() => onRowClick(cell.cell_id)}
                      className={`
                        cursor-pointer transition-all border-b border-slate-800/50 last:border-0
                        ${
                          isSelected
                            ? 'bg-cyan-500/10 hover:bg-cyan-500/20'
                            : 'hover:bg-slate-800/50'
                        }
                      `}
                    >
                      <td className="px-4 py-2 font-mono text-white">
                        {cell.cell_id}
                      </td>
                      <td
                        className={`px-4 py-2 font-mono font-semibold ${
                          cell.suhii_night >= 3
                            ? 'text-red-400'
                            : cell.suhii_night >= 1
                            ? 'text-orange-400'
                            : 'text-slate-400'
                        }`}
                      >
                        {cell.suhii_night >= 0 ? '+' : ''}
                        {cell.suhii_night.toFixed(1)}°C
                      </td>
                      <td className="px-4 py-2 font-mono text-slate-400">
                        {cell.suhii_day >= 0 ? '+' : ''}
                        {cell.suhii_day.toFixed(1)}°C
                      </td>
                      <td className="px-4 py-2 font-mono text-slate-300">
                        {(cell.frac_built * 100).toFixed(0)}%
                      </td>
                      <td
                        className={`px-4 py-2 font-mono ${
                          cell.frac_tree >= 0.2
                            ? 'text-emerald-400'
                            : 'text-slate-400'
                        }`}
                      >
                        {(cell.frac_tree * 100).toFixed(0)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function SortHeader({
  label,
  active,
  dir,
  onClick,
}: {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
}) {
  return (
    <th
      className="text-left px-4 py-2 text-slate-500 font-medium cursor-pointer hover:text-white transition-all"
      onClick={onClick}
    >
      <div className="flex items-center gap-1">
        {label}
        {active ? (
          dir === 'desc' ? (
            <ChevronDown className="w-3 h-3 text-cyan-400" />
          ) : (
            <ChevronUp className="w-3 h-3 text-cyan-400" />
          )
        ) : (
          <ChevronsUpDown className="w-3 h-3 opacity-30" />
        )}
      </div>
    </th>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        px-2.5 py-1 rounded-md text-[11px] font-medium transition-all
        ${
          active
            ? 'bg-cyan-500 text-white'
            : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
        }
      `}
    >
      {children}
    </button>
  );
}
