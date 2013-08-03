%define svn 0
%define snapshot 20130418

Name: cp2k
Version: 2.4
Release: 6%{?dist}
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
Source4: cp2k-snapshot.sh
# patch to:
# use rpm optflags
# link with atlas instead of vanilla blas/lapack
# build with libint and libxc
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
Obsoletes: %{name}-smp < 2.4-3
Provides: %{name}-smp = %{version}-%{release}
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

This package contains the non-MPI single process and multi-threaded versions.

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

This package contains the parallel single- and multi-threaded versions
using OpenMPI.

%package mpich
Group: Applications/Engineering
Summary: Molecular simulations software - mpich version
BuildRequires:  mpich-devel
BuildRequires:  blacs-mpich-devel
BuildRequires:  scalapack-mpich-devel
Requires: %{name}-common = %{version}-%{release}
Requires: blacs-mpich
Requires: scalapack-mpich
Provides: %{name}-mpich2 = %{version}-%{release}
Obsoletes: %{name}-mpich2 < 2.4-5

%description mpich
%{cp2k_desc_base}

This package contains the parallel single- and multi-threaded versions
using mpich.

%package common
Group: Applications/Engineering
Summary: Molecular simulations software - common files

%description common
%{cp2k_desc_base}

This package contains the documentation and the manual.

%prep
%setup -q
TARGET=$(tools/get_arch_code)
%ifnarch x86_64
ln -s Linux-x86-64-gfortran.sopt arch/${TARGET}.sopt
ln -s Linux-x86-64-gfortran.ssmp arch/${TARGET}.ssmp
%endif
ln -s Linux-x86-64-gfortran.popt arch/${TARGET}-openmpi.popt
ln -s Linux-x86-64-gfortran.popt arch/${TARGET}-mpich.popt
ln -s Linux-x86-64-gfortran.psmp arch/${TARGET}-openmpi.psmp
ln -s Linux-x86-64-gfortran.psmp arch/${TARGET}-mpich.psmp
%patch0 -p1 -b .r
rm -r tools/makedepf90
chmod -x src/harris_{functional,{env,energy}_types}.F
# fix crashes in fftw on i686
%ifarch i686
sed -i 's/-D__FFTW3/-D__FFTW3 -D__FFTW3_UNALIGNED/g' arch/Linux-i686-gfortran*
%endif

%build
TARGET=$(tools/get_arch_code)
pushd makefiles
    %{_openmpi_load}
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="${TARGET}-openmpi" VERSION=popt
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="${TARGET}-openmpi" VERSION=psmp
    %{_openmpi_unload}
    %{_mpich_load}
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="${TARGET}-mpich" VERSION=popt
        make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} ARCH="${TARGET}-mpich" VERSION=psmp
    %{_mpich_unload}

    make OPTFLAGS="%{optflags} -L%{_libdir}/atlas" %{?_smp_mflags} sopt ssmp
popd

%install
TARGET=$(tools/get_arch_code)
install -d %{buildroot}%{_bindir}
%{_openmpi_load}
    mkdir -p %{buildroot}%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/
    install -pm755 exe/${TARGET}-openmpi/cp2k.popt %{buildroot}%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.popt_openmpi
    install -pm755 exe/${TARGET}-openmpi/cp2k.psmp %{buildroot}%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.psmp_openmpi
%{_openmpi_unload}
%{_mpich_load}
    mkdir -p %{buildroot}%{_libdir}/mpich%{?_opt_cc_suffix}/bin/
    install -pm755 exe/${TARGET}-mpich/cp2k.popt %{buildroot}%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.popt_mpich
    install -pm755 exe/${TARGET}-mpich/cp2k.psmp %{buildroot}%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.psmp_mpich
%{_mpich_unload}
install -pm755 exe/${TARGET}/cp2k.sopt %{buildroot}%{_bindir}
install -pm755 exe/${TARGET}/cp2k.ssmp %{buildroot}%{_bindir}

%clean
rm -rf %{buildroot}

%if 1
%check
cat > tests/fedora.config << __EOF__
export LC_ALL=C
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
%{_bindir}/cp2k.ssmp

%files openmpi
%defattr(-,root,root,-)
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.popt_openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/cp2k.psmp_openmpi

%files mpich
%defattr(-,root,root,-)
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.popt_mpich
%{_libdir}/mpich%{?_opt_cc_suffix}/bin/cp2k.psmp_mpich

%changelog
* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jul 20 2013 Deji Akingunola <dakingun@gmail.com> - 2.4-5
- Rename mpich2 sub-packages to mpich and rebuild for mpich-3.0

* Sun Jul 14 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-4
- rebuild for new OpenMPI

* Tue Jul 02 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-3
- build psmp variants (MPI+OpenMP)
- move ssmp build to main package and drop smp subpackage
- drop local config files, patch upstream's and symlink when necessary
- save the output of tools/get_arch_code and re-use it

* Wed Jun 19 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-2
- add MPI implementation suffix back to MPI binaries (required by guidelines)

* Mon Jun 17 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-1
- update to 2.4 release
- drop gfortran-4.8 patch (fixed upstream)
- reorder libraries in LDFLAGS again to follow current upstream config
- rename both MPI binaries to cp2k.popt

* Thu Apr 18 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.5.20130418
- correct SVN url in snapshot script
- update to current SVN trunk (r12842)
- use (and patch) upstream-provided configs for x86_64 ssmp and popt builds
- no need to force FC=gfortran anymore

* Wed Apr 17 2013 Dominik Mierzejewski <rpm@greysector.net> - 2.4-0.4.20130220
- fix build with gfortran-4.8 (bug #913927)
- link with libf77blas for MPI builds to avoid undefined reference to symbol 'dgemm_'

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
