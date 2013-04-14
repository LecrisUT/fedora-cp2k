%define svn 1
%define snapshot 20130220

Name: cp2k
Version: 2.4
Release: 0.3.%{snapshot}%{?dist}
Group: Applications/Engineering
Summary: A molecular dynamics engine capable of classical and Car-Parrinello simulations
License: GPLv2+
URL: http://cp2k.org/
%if %{svn}
# run cp2k-snapshot.sh to produce this
Source0: cp2k-%{version}-%{snapshot}.tar.bz2
%else
Source0: http://downloads.sourceforge.net/project/cp2k/cp2k-%{version}.tar.bz2
%endif
# custom openmpi arch file
# also works for mpich2 and possibly others
# only assumption for mpi library: fortran compiler is named mpif90
Source1: Linux-gfortran-openmpi.popt
Source2: Linux-gfortran.ssmp
Source3: Linux-i686-gfortran.sopt
Source4: cp2k-snapshot.sh
# patch to:
# use rpm optflags
# link with atlas instead of vanilla blas/lapack
# link with libint
# use external makedepf90
# skip compilation during regtests
Patch0: %{name}-rpm.patch
BuildRequires: atlas-devel
# for regtests
BuildRequires: bc
BuildRequires: fftw-devel
BuildRequires: gcc-gfortran
BuildRequires: libint-devel >= 1.1.4
BuildRequires: libxc-devel
BuildRequires: makedepf90
BuildRequires: /bin/hostname
Requires: %{name}-common = %{version}-%{release}
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%global cp2k_desc_base \
CP2K is a freely available (GPL) program, written in Fortran 95, to\
perform atomistic and molecular simulations of solid state, liquid,\
molecular and biological systems. It provides a general framework for\
different methods such as e.g. density functional theory (DFT) using a\
mixed Gaussian and plane waves approach (GPW), and classical pair and\
many-body potentials.

%description
%{cp2k_desc_base}

This package contains the single process version.

%package smp
Group: Applications/Engineering
Summary: Molecular simulations software - OpenMP version
Requires: %{name}-common = %{version}-%{release}

%description smp
%{cp2k_desc_base}

This package contains the multi-threaded version (using OpenMP).

%package openmpi
Group: Applications/Engineering
Summary: Molecular simulations software - openmpi version
BuildRequires:  openmpi-devel
BuildRequires:  blacs-openmpi-devel
BuildRequires:  scalapack-openmpi-devel
Requires: %{name}-common = %{version}-%{release}
Requires: blacs-openmpi
Requires: scalapack-openmpi

%description openmpi
%{cp2k_desc_base}

This package contains the multi-threaded version (using OpenMPI).

%package mpich2
Group: Applications/Engineering
Summary: Molecular simulations software - mpich2 version
BuildRequires:  mpich2-devel
BuildRequires:  blacs-mpich2-devel
BuildRequires:  scalapack-mpich2-devel
Requires: %{name}-common = %{version}-%{release}
Requires: blacs-mpich2
Requires: scalapack-mpich2

%description mpich2
%{cp2k_desc_base}

This package contains the multi-threaded version (using mpich2).

%package common
Group: Applications/Engineering
Summary: Molecular simulations software - common files

%description common
%{cp2k_desc_base}

This package contains the documentation and the manual.

%prep
%setup -q
cp -p %{SOURCE1} arch/
cp -p %{SOURCE1} arch/Linux-gfortran-mpich2.popt
cp -p %{SOURCE2} arch/Linux-i686-gfortran.ssmp
cp -p %{SOURCE2} arch/Linux-x86-64-gfortran.ssmp
cp -p %{SOURCE3} arch/
%patch0 -p1 -b .r
rm -r tools/makedepf90
chmod -x src/harris_{functional,{env,energy}_types}.F
# fix crashes in fftw on i686
%ifarch i686
sed -i 's/-D__FFTW3/-D__FFTW3 -D__FFTW3_UNALIGNED/g' arch/Linux-i686-gfortran* arch/Linux-gfortran-{mpich2,openmpi}.popt
%endif

%build
export FORT_C_NAME=gfortran
pushd makefiles
    %{_openmpi_load}
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="Linux-gfortran-openmpi" VERSION=popt
    %{_openmpi_unload}
    %{_mpich2_load}
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="Linux-gfortran-mpich2" VERSION=popt
    %{_mpich2_unload}

    make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} sopt ssmp
popd

%install
rm -rf %{buildroot}
export FORT_C_NAME=gfortran
install -d %{buildroot}%{_bindir}
%{_openmpi_load}
    mkdir -p %{buildroot}%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/
    install -pm755 exe/Linux-gfortran-openmpi/cp2k.popt %{buildroot}%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.popt_openmpi
%{_openmpi_unload}
%{_mpich2_load}
    mkdir -p %{buildroot}%{_libdir}/mpich2%{?_opt_cc_suffix}/bin/
    install -pm755 exe/Linux-gfortran-mpich2/cp2k.popt %{buildroot}%{_libdir}/mpich2%{?_opt_cc_suffix}/bin/cp2k.popt_mpich2
%{_mpich2_unload}
install -pm755 exe/`tools/get_arch_code`/cp2k.sopt %{buildroot}%{_bindir}
install -pm755 exe/`tools/get_arch_code`/cp2k.ssmp %{buildroot}%{_bindir}

%clean
rm -rf %{buildroot}

%if 1
%check
export FORT_C_NAME=gfortran
cat > tests/fedora.config << __EOF__
export LC_ALL=C
export FORT_C_NAME=gfortran
dir_base=%{_builddir}
cp2k_version=sopt
dir_triplet=`tools/get_arch_code`
cp2k_dir=cp2k-%{version}
maxtasks=`getconf _NPROCESSORS_ONLN`
emptycheck="NO"
leakcheck="NO"
__EOF__
pushd tests
../tools/do_regtest -config fedora.config
popd
%endif

%files common
%defattr(-,root,root,-)
%doc COPYRIGHT README doc/tutorialCp2k.html

%files
%defattr(-,root,root,-)
%{_bindir}/cp2k.sopt

%files smp
%defattr(-,root,root,-)
%{_bindir}/cp2k.ssmp

%files openmpi
%defattr(-,root,root,-)
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.popt_openmpi

%files mpich2
%defattr(-,root,root,-)
%{_libdir}/mpich2%{?_opt_cc_suffix}/bin/cp2k.popt_mpich2

%changelog
* Sun Apr 14 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.3.20130220
- fix crashes in fftw on i686 (patch by Michael Banck)

* Fri Feb 22 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.2.20130220
- add requires for respective blacs and scalapack versions

* Wed Feb 20 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.1.20130220
- re-enable regtests
- update to current SVN trunk (2.4)
- drop svn patch (no longer needed)
- link with libfftw3_omp for ssmp build
- reorder libraries in LDFLAGS per M. Guidon's cp2k installation primer
- add -ffree-line-length-none to Fortran flags
- add a patch to echo the name of reach test (from Debian package)
- build with libxc
- update libint/libderiv options to match current builds

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Dec 26 2012 Kevin Fenzi <kevin@scrye.com> 2.3-2
- Rebuild for new libmpich

* Wed Sep 05 2012 Dominik Mierzejewski <rpm@greysector.net> - 2.3-1
- updated to 2.3 release

* Sun Aug 26 2012 Dominik Mierzejewski <rpm@greysector.net> - 2.3-0.20120825
- updated to current 2.3 branch (trunk)
- added snapshot creator script
- moved new files out of -rpm patch and into separate SourceN entries
- dropped non-standard compiler flags from MPI builds

* Wed Jul 25 2012 Jussi Lehtola <jussilehtola@fedoraproject.org> - 2.1-7.20101006
- Rebuild due to changed libint.

* Tue Jul 24 2012 Thomas Spura <tomspur@fedoraproject.org> - 2.1-6.20101006
- don't run testsuite as it is only usefull when comparing to old outputs
  (which we don't have at buildtime)
- define common description macro
- also build with openmpi/mpich2
- new url

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-5.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-4.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1-3.20101006
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Dec 07 2010 Dominik Mierzejewski <rpm@greysector.net> 2.1-2.20101006
- make Summary more descriptive
- use atlas instead of blas/lapack
- pass special CFLAGS to support libint's higher values of angular momentum

* Fri Dec 03 2010 Dominik Mierzejewski <rpm@greysector.net> 2.1-1.20101006
- initial package
