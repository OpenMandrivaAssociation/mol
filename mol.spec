# kernel-source-2.6.21.2mdv
%define kver 2.6.21
%define krelease 2mdv
%define kversion %{kver}-%{krelease}
%define kname %{kver}.%{krelease}
%define kernel_tree %{_builddir}/mol-%{source_version}%{source_pre}/linux-%{kversion}
# default is to build mol and build kmods
# use --without mol to disable mol build
# use --without kmods to disable kmods build
%define build_kmods 1
%define build_mol 1
%{?_without_mol: %global build_mol 0}
%{?_without_kmods: %global build_kmods 0}
%{?_with_mol: %global build_mol 1}
%{?_with_kmods: %global build_kmods 1}

%define source_version 0.9.72.1
%define source_pre %{nil}
%define package_version 0.9.72.1

Summary:	Native MacOS emulator
Name:		mol
Version:	%{package_version}
Release:	%mkrel 5
License:	GPL
Group:		Emulators
Source:		http://www.maconlinux.com/downloads/%{name}-%{source_version}%{source_pre}.tar.bz2
Source1: 	mol_16.png
Source2: 	mol_32.png
Source3: 	mol_48.png
Patch2:		mol-0.9.71-kmod-unresolved-symbols.patch
URL:		https://www.maconlinux.com/
BuildRoot:	%_tmppath/%{name}-%{version}-root
BuildRequires:	X11-devel png-devel
Requires: 	mol-kernel-modules
ExclusiveArch:	ppc

%description
With MOL you can run MacOS under Linux - in full speed!
All PowerPC versions of MacOS are supported, including OS/X.

%package kmods
Summary:        Mac-on-Linux kernel modules
Group:          Emulators
Provides:       mol-kernel-modules
BuildRequires:	kernel-source-%{kname}
BuildRequires:	bison flex
BuildConflicts:	kernel-source-stripped-%{kname}
Requires:	kernel-%{kname}

%description kmods
This package contains the Mac-on-Linux kernel module
needed by MOL. It also contains the networking kernel
modules. Built for: kernel-%{kname}.

%prep

%setup -q -n %{name}-%{source_version}%{source_pre}
%patch2 -p1 -b .unresolved-symbols

# (sb) copy kernel-source tree, so we can build as a normal user
# this will fail if permissions are too restrictive on kernel-source
%if %build_kmods
cp -ar %{_prefix}/src/linux-%{kversion} .
perl -pi -e 's|mdkcustom|mdk|' linux-%{kversion}/Makefile 
chmod -R +w linux-%{kversion}
%endif

#change default molrc.video to disable console mode for automagic setup
perl -pi -e 's|enable_console_video:\tyes|enable_console_video:\tno|g' Doc/config/molrc.video

%build
./configure \
        --prefix=/usr \
        --exec-prefix=/usr \
        --bindir=/usr/bin \
        --sbindir=/usr/sbin \
        --sysconfdir=/etc \
        --datadir=/usr/share \
        --includedir=/usr/include \
        --libdir=%{_libdir} \
        --libexecdir=%{_libdir} \
        --localstatedir=/var/lib \
        --sharedstatedir=/usr/com \
        --mandir=/usr/share/man \
        --infodir=/usr/share/info
make defconfig
make clean

%if build_mol
%make BUILD_MODS=n prefix=%{_prefix}
%endif

# (sb) kernel modules build
# (cjw) build for all 2.6 flavors except *BOOT
%if %build_kmods
if [ -d "%kernel_tree" ]
then
	rm -f %{kernel_tree}/arch/ppc/defconfig-maximum
	rm -f %{kernel_tree}/arch/ppc/defconfig-BOOT
	rm -f %{kernel_tree}/arch/ppc/defconfig-power4BOOT
	rm -rf %{_builddir}/ktrees
	mkdir %{_builddir}/ktrees
	for i in  %{kernel_tree}/arch/ppc/defconfig* ; do
		base=`basename $i`
		ver=`echo $base |awk -F- '{print $2 }'`;
		cp -al %{kernel_tree} %{_builddir}/ktrees/$base
		pushd %{_builddir}/ktrees/$base
        perl -p -i -e "s/^EXTRAVERSION[^.]*(\.[0-9]+)?-.*\$/EXTRAVERSION = \$1-%{krelease}$ver/" Makefile 
		make mrproper > /dev/null
		cp $i .config
		make oldconfig > /dev/null 2>&1
		make include/linux/version.h
		make include/asm
		make scripts
		popd
		make modules NETMODS=y KERNEL_TREES=%{_builddir}/ktrees/$base
	done
	rm -rf %{_builddir}/ktrees %{kernel_tree}
fi
%endif 

%install
rm -fr %buildroot
%if build_mol
%makeinstall_std prefix=%{_prefix}
# (sb) move the docs and let rpm install them
rm -fr moldoc
mv -f $RPM_BUILD_ROOT/usr/share/doc/mol-%{source_version} moldoc

mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/mandriva-%{name}.desktop << EOF
[Desktop Entry]
Name=MOL
Comment=Run MacOS in the Mac On Linux PowerPC virtualization environment
Exec=%{_bindir}/startmol
Icon=%{name}
Terminal=false
Type=Application
Categories=System;Emulator;X-MandrivaLinux-MoreApplications-Emulators;

[Desktop Entry]
Name=MOL OSX
Comment=Run MacOS X in the Mac On Linux PowerPC virtualization environment
Exec=%{_bindir}/startmol --osx
Icon=%{name}    
Terminal=false
Type=Application
Categories=System;Emulator;X-MandrivaLinux-MoreApplications-Emulators;
EOF

mkdir -p  $RPM_BUILD_ROOT%{_miconsdir} $RPM_BUILD_ROOT%{_liconsdir}
cp %{SOURCE1} $RPM_BUILD_ROOT%{_miconsdir}/%{name}.png
cp %{SOURCE2} $RPM_BUILD_ROOT%{_iconsdir}/%{name}.png
cp %{SOURCE3} $RPM_BUILD_ROOT%{_liconsdir}/%{name}.png
%endif

%if %build_kmods
# (sb) install kernel modules if we built them
make install-modules DESTDIR=$RPM_BUILD_ROOT prefix=%{_prefix}
%endif

# (sb) unpackaged files
%if !%build_mol
rm -fr $RPM_BUILD_ROOT/%{_bindir}
rm -fr $RPM_BUILD_ROOT/%{_datadir}
rm -fr $RPM_BUILD_ROOT/%{_localstatedir}/lib
rm -fr $RPM_BUILD_ROOT/%{_sysconfdir}
rm -fr $RPM_BUILD_ROOT/%{_menudir}
rm -fr $RPM_BUILD_ROOT/%{_libdir}/%{name}/%{source_version}/bin
rm -fr $RPM_BUILD_ROOT/%{_libdir}/%{name}/%{source_version}/%{name}*
%endif
%if !%build_kmods
rm -fr $RPM_BUILD_ROOT/%{_libdir}/%{name}/%{source_version}/modules/*
%endif

%if %mdkversion < 200900
%post
%update_menus
%endif

%if %mdkversion < 200900
%postun
%clean_menus
%endif

%post kmods
if [ ! -e /dev/sheep_net ]; then
mknod /dev/sheep_net c 10 198
fi

%clean
rm -fr %buildroot

%define _mol_libdir             %{_libdir}/mol/%{source_version}
%define _mol_datadir            %{_datadir}/mol/%{source_version}
%define _mol_localstatedir      %{_localstatedir}/lib/mol

%if %build_mol
%files
%defattr(-,root,root)
%doc moldoc
%dir %_sysconfdir/mol
%config(noreplace) %_sysconfdir/mol/session.map
%config(noreplace) %_sysconfdir/mol/tunconfig
%config(noreplace) %_sysconfdir/mol/dhcpd-mol.conf
%config(noreplace) %_sysconfdir/mol/molrc.input
%config(noreplace) %_sysconfdir/mol/molrc.linux
%config(noreplace) %_sysconfdir/mol/molrc.macos
%config(noreplace) %_sysconfdir/mol/molrc.video
%config(noreplace) %_sysconfdir/mol/molrc.net
%config(noreplace) %_sysconfdir/mol/molrc.ow
%config(noreplace) %_sysconfdir/mol/molrc.osx
%config(noreplace) %_sysconfdir/mol/yaboot.conf
%config(noreplace) %_sysconfdir/mol/molrc.sound

%_mol_localstatedir/nvram.nw

%_mandir/man?/*

%_bindir/startmol
%_bindir/molvconfig
%_bindir/molrcget
%_bindir/mol-img

%dir %_mol_libdir
%dir %_mol_datadir
%dir %_mol_localstatedir
%_mol_libdir/bin
%_mol_libdir/mol.symbols

%_mol_datadir/images
%_mol_datadir/oftrees
%_mol_datadir/drivers
%_mol_datadir/syms
%_mol_datadir/vmodes
%_mol_datadir/nvram
%_mol_datadir/graphics
%_mol_datadir/startboing

%dir %_mol_datadir/config
%_mol_datadir/config/molrc.sys
%_mol_datadir/config/molrc.post

%_mol_localstatedir/nvram.x

%{_datadir}/applications/mandriva-mol.desktop
%{_iconsdir}/*.png
%{_miconsdir}/*.png
%{_liconsdir}/*.png
%endif

%if %build_kmods
%files kmods
%defattr(-,root,root)
%_mol_libdir/modules/*
%endif

