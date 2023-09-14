%global git 0
%global snapshot 20210528
%global commit 056df937c4510a5ec8564bca4ce4b33f44aec9b8
%global shortcommit %(c=%{commit}; echo ${c:0:7})

%bcond_without check
%global mpi_list openmpi mpich

Name:     cp2k
Version:  2023.2
Release:  %autorelease
Summary:  Ab Initio Molecular Dynamics
License:  GPL-2.0-or-later
URL:      https://cp2k.org/

%if %{git}
Source: https://github.com/cp2k/cp2k/archive/%{commit}/cp2k-%{shortcommit}.tar.gz
%else
Source: https://github.com/cp2k/cp2k/releases/download/v%{version}/cp2k-%{version}.tar.bz2
%endif

BuildRequires: flexiblas-devel
# for regtests
BuildRequires: libomp-devel
BuildRequires: fftw-devel
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: gcc-gfortran
BuildRequires: ninja-build
BuildRequires: libxc-devel
BuildRequires: libxsmm-devel
BuildRequires: python3-fypp
BuildRequires: spglib-devel
BuildRequires: dbcsr-devel
# TODO: Add python bindings
#BuildRequires: python3-devel
# openmpi
BuildRequires:  openmpi-devel
BuildRequires:  dbcsr-openmpi-devel
BuildRequires:  elpa-openmpi-devel
## TODO: Add scalapack support
#BuildRequires:  scalapack-openmpi-devel
# mpich
BuildRequires:  mpich-devel
BuildRequires:  dbcsr-mpich-devel
BuildRequires:  elpa-mpich-devel
## TODO: Add scalapack support
#BuildRequires:  scalapack-mpich-devel

# Libint can break the API between releases
Requires: cp2k-common = %{version}-%{release}

%global cp2k_desc_base \
CP2K is a freely available (GPL) program, written in Fortran 95, to\
perform atomistic and molecular simulations of solid state, liquid,\
molecular and biological systems. It provides a general framework for\
different methods such as e.g. density functional theory (DFT) using a\
mixed Gaussian and plane waves approach (GPW), and classical pair and\
many-body potentials.\
\
CP2K does not implement Car-Parinello Molecular Dynamics (CPMD).

%description
%{cp2k_desc_base}

This package contains the non-MPI single process and multi-threaded versions.

%package openmpi
Summary: Molecular simulations software - openmpi version
Requires: cp2k-common = %{version}-%{release}

%description openmpi
%{cp2k_desc_base}

This package contains the parallel single- and multi-threaded versions
using OpenMPI.

%package mpich
Summary: Molecular simulations software - mpich version
Requires: cp2k-common = %{version}-%{release}

%description mpich
%{cp2k_desc_base}

This package contains the parallel single- and multi-threaded versions
using mpich.

%package common
Summary: Molecular simulations software - common files

%description common
%{cp2k_desc_base}

This package contains the documentation and the manual.


%prep
%if %{git}
%autosetup -n cp2k-%{commit}
%else
%autosetup -n cp2k-%{version}
%endif
# Remove bundled fypp and dbcsr so that it is not accidentally picked up
rm tools/build_utils/fypp
rm -r exts/dbcsr


%build
# Prepare for mpi
source /etc/profile.d/modules.sh
# Note: The following works beause:
# - %%global: macros are evaluated explicitly at definition, $variables are not expanded
# - %%define: macros are evaluated in-place, $variables are also expanded
%global _vpath_builddir %{_target_platform}_${mpi:-serial}

for mpi in %{mpi_list} ''; do
  %define mpi $mpi
  %{?mpi:%{_%{mpi}_load}}
  # TODO: Remove CP2K_BUILD_DBSCR when dbscr is packaged
  %cmake \
    -G Ninja \
    -DCMAKE_C_STANDARD=17 \
    -DCP2K_BLAS_VENDOR=FlexiBLAS \
    -DCP2K_USE_LIBXC=ON \
    -DCP2K_USE_SPGLIB=ON \
    -DCP2K_USE_LIBXSMM=ON \
    %{?$mpi:-DCP2K_USE_ELPA=ON} \
    -DCP2K_USE_FFTW3=ON \
    -DCP2K_USE_MPI=%{?mpi:ON}%{!?mpi:OFF} \
    %{?mpi:-DCMAKE_INSTALL_LIBDIR=$MPI_LIB}
  %cmake_build
  %{?mpi:%{_%{mpi}_unload}}
  %undefine mpi
done


%install
for mpi in %{mpi_list} ''; do
  %cmake_install
done


%if %{with check}
# regtests take ~12 hours on aarch64 and ~48h on s390x
%check
for mpi in %{mpi_list} ''; do
  %define mpi $mpi
  %{?mpi:%{_%{mpi}_load}}
  %ctest
  %{?mpi:%{_%{mpi}_unload}}
  %undefine mpi
done
%endif

%files common
%license LICENSE
%doc README.md
%{_datadir}/cp2k

%files
%{_bindir}/cp2k.sopt
%{_bindir}/cp2k.ssmp
%{_bindir}/cp2k_shell.ssmp
%dir %{_libdir}/cp2k
%{_libdir}/cp2k/lib*.so

%files openmpi
%{_libdir}/openmpi/bin/cp2k.popt_openmpi
%{_libdir}/openmpi/bin/cp2k.psmp_openmpi
%{_libdir}/openmpi/bin/cp2k_shell.psmp_openmpi
%dir %{_libdir}/openmpi/lib/cp2k
%{_libdir}/openmpi/lib/cp2k/lib*.so

%files mpich
%{_libdir}/mpich/bin/cp2k.popt_mpich
%{_libdir}/mpich/bin/cp2k.psmp_mpich
%{_libdir}/mpich/bin/cp2k_shell.psmp_mpich
%dir %{_libdir}/mpich/lib/cp2k
%{_libdir}/mpich/lib/cp2k/lib*.so

%changelog
%autochangelog
